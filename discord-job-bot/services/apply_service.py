import os
import asyncio
import logging
import uuid
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from config.settings import settings
from database.models import UserProfile, CachedJob, JobApplication, ApplyStatus, ApplyType
from services.profile_service import profile_service

logger = logging.getLogger(__name__)

class ApplyService:
    def __init__(self):
        self.semaphore = asyncio.Semaphore(settings.MAX_CONCURRENT_APPLICATIONS)

    async def execute_application(
        self,
        db: AsyncSession,
        user: UserProfile,
        job: CachedJob,
        auto_submit: bool = True
    ) -> Dict[str, Any]:
        """Orchestrate automated application submission based on target job type."""
        async with self.semaphore:
            # 1. Create initial application record
            application = JobApplication(
                discord_id=user.discord_id,
                job_id=job.job_id,
                job_title=job.title,
                company_name=job.company,
                apply_type=job.apply_type,
                status=ApplyStatus.IN_PROGRESS.value,
                applied_at=datetime.now(timezone.utc)
            )
            db.add(application)
            await db.flush()

            # 2. Check prerequisites (e.g. resume)
            if not user.resume_file_path or not os.path.exists(user.resume_file_path):
                application.status = ApplyStatus.FAILED.value
                application.error_message = "No resume uploaded. Please use `/profile setup` to upload your PDF resume first."
                await db.commit()
                return {
                    "success": False,
                    "status": ApplyStatus.FAILED.value,
                    "message": application.error_message,
                    "screenshot_path": None,
                    "apply_url": job.apply_url
                }

            # 3. Route by apply type
            try:
                if job.apply_type == ApplyType.LINKEDIN_EASY_APPLY.value or "linkedin.com" in job.apply_url.lower():
                    result = await self._apply_linkedin_easy(user, job, auto_submit)
                elif job.apply_type == ApplyType.ATS_PORTAL.value or any(k in job.apply_url.lower() for k in ["greenhouse.io", "lever.co"]):
                    result = await self._apply_ats_portal(user, job, auto_submit)
                else:
                    # External direct portal
                    result = {
                        "success": True,
                        "status": ApplyStatus.MANUAL_REQUIRED.value,
                        "message": "This job requires external portal submission. Please follow the direct application link.",
                        "screenshot_path": None,
                        "apply_url": job.apply_url
                    }

                application.status = result.get("status", ApplyStatus.SUBMITTED.value)
                application.screenshot_path = result.get("screenshot_path")
                application.error_message = result.get("error")
                application.notes = result.get("message")
                await db.commit()
                return result

            except Exception as e:
                logger.error(f"Application error for job {job.job_id}: {e}", exc_info=True)
                application.status = ApplyStatus.FAILED.value
                application.error_message = str(e)
                await db.commit()
                return {
                    "success": False,
                    "status": ApplyStatus.FAILED.value,
                    "message": f"Automated application encountered an issue: {str(e)}",
                    "screenshot_path": None,
                    "apply_url": job.apply_url
                }

    async def _apply_linkedin_easy(
        self,
        user: UserProfile,
        job: CachedJob,
        auto_submit: bool
    ) -> Dict[str, Any]:
        """Automate LinkedIn Easy Apply via headless Playwright browser."""
        from playwright.async_api import async_playwright
        
        screenshot_filename = f"apply_linkedin_{user.discord_id}_{uuid.uuid4().hex[:6]}.png"
        screenshot_path = str(settings.SCREENSHOT_STORAGE_DIR / screenshot_filename)
        
        li_cookie = profile_service.get_decrypted_linkedin_cookie(user)

        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=settings.HEADLESS_BROWSER,
                args=["--no-sandbox", "--disable-dev-shm-usage", "--disable-gpu"]
            )
            context = await browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                viewport={"width": 1280, "height": 800}
            )

            # If user provided session cookie, inject it
            if li_cookie:
                await context.add_cookies([
                    {
                        "name": "li_at",
                        "value": li_cookie,
                        "domain": ".www.linkedin.com",
                        "path": "/",
                        "httpOnly": True,
                        "secure": True,
                        "sameSite": "None"
                    }
                ])

            page = await context.new_page()
            try:
                await page.goto(job.apply_url, timeout=settings.BROWSER_TIMEOUT_MS, wait_until="domcontentloaded")
                await asyncio.sleep(2)

                # Look for Easy Apply button
                easy_apply_btn = page.locator("button.jobs-apply-button, button:has-text('Easy Apply'), button:has-text('Apply now')")
                if await easy_apply_btn.count() > 0:
                    await easy_apply_btn.first.click()
                    await asyncio.sleep(1.5)

                    # Multi-step dialog handler (Phone / Resume / Next)
                    for step in range(5):
                        # Fill phone if input exists
                        phone_input = page.locator("input[id*='phoneNumber'], input[id*='phone-number']")
                        if await phone_input.count() > 0 and user.phone:
                            curr_val = await phone_input.first.input_value()
                            if not curr_val:
                                await phone_input.first.fill(user.phone)

                        # Handle resume upload file chooser
                        upload_input = page.locator("input[type='file']")
                        if await upload_input.count() > 0 and user.resume_file_path:
                            await upload_input.first.set_input_files(user.resume_file_path)
                            await asyncio.sleep(1)

                        # Look for Next or Review button
                        next_btn = page.locator("button:has-text('Next'), button:has-text('Review')")
                        if await next_btn.count() > 0 and await next_btn.first.is_enabled():
                            await next_btn.first.click()
                            await asyncio.sleep(1.5)
                        else:
                            break

                    # Check for Submit Application button
                    submit_btn = page.locator("button:has-text('Submit application')")
                    if await submit_btn.count() > 0 and auto_submit:
                        await submit_btn.first.click()
                        await asyncio.sleep(2)

                    # Capture confirmation screenshot
                    await page.screenshot(path=screenshot_path, full_page=False)
                    await browser.close()

                    return {
                        "success": True,
                        "status": ApplyStatus.SUBMITTED.value,
                        "message": "LinkedIn Easy Apply submitted successfully!",
                        "screenshot_path": screenshot_path,
                        "apply_url": job.apply_url
                    }
                else:
                    # Capture current state screenshot
                    await page.screenshot(path=screenshot_path, full_page=False)
                    await browser.close()
                    return {
                        "success": True,
                        "status": ApplyStatus.MANUAL_REQUIRED.value,
                        "message": "Login or manual verification required for Easy Apply on LinkedIn. Please check the direct link.",
                        "screenshot_path": screenshot_path,
                        "apply_url": job.apply_url
                    }

            except Exception as e:
                await page.screenshot(path=screenshot_path, full_page=False)
                await browser.close()
                return {
                    "success": False,
                    "status": ApplyStatus.FAILED.value,
                    "message": f"LinkedIn Easy Apply error: {str(e)}",
                    "screenshot_path": screenshot_path,
                    "apply_url": job.apply_url
                }

    async def _apply_ats_portal(
        self,
        user: UserProfile,
        job: CachedJob,
        auto_submit: bool
    ) -> Dict[str, Any]:
        """Automate ATS form submissions (Greenhouse / Lever)."""
        from playwright.async_api import async_playwright
        
        screenshot_filename = f"apply_ats_{user.discord_id}_{uuid.uuid4().hex[:6]}.png"
        screenshot_path = str(settings.SCREENSHOT_STORAGE_DIR / screenshot_filename)

        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=settings.HEADLESS_BROWSER,
                args=["--no-sandbox", "--disable-dev-shm-usage"]
            )
            context = await browser.new_context(viewport={"width": 1280, "height": 800})
            page = await context.new_page()

            try:
                await page.goto(job.apply_url, timeout=settings.BROWSER_TIMEOUT_MS, wait_until="domcontentloaded")
                await asyncio.sleep(2)

                # Name parsing
                first_name = user.full_name.split()[0] if user.full_name else "Candidate"
                last_name = " ".join(user.full_name.split()[1:]) if user.full_name and len(user.full_name.split()) > 1 else ""

                # Fill Standard First & Last Name or Full Name fields
                first_name_input = page.locator("input[name*='first_name'], input[id*='first_name']")
                if await first_name_input.count() > 0:
                    await first_name_input.first.fill(first_name)

                last_name_input = page.locator("input[name*='last_name'], input[id*='last_name']")
                if await last_name_input.count() > 0:
                    await last_name_input.first.fill(last_name)

                full_name_input = page.locator("input[name*='name']:not([name*='first']):not([name*='last']), input[id*='name']:not([id*='first']):not([id*='last'])")
                if await full_name_input.count() > 0 and user.full_name:
                    await full_name_input.first.fill(user.full_name)

                # Fill Email
                email_input = page.locator("input[type='email'], input[name*='email'], input[id*='email']")
                if await email_input.count() > 0 and user.email:
                    await email_input.first.fill(user.email)

                # Fill Phone
                phone_input = page.locator("input[type='tel'], input[name*='phone'], input[id*='phone']")
                if await phone_input.count() > 0 and user.phone:
                    await phone_input.first.fill(user.phone)

                # Fill LinkedIn URL
                linkedin_input = page.locator("input[name*='linkedin'], input[id*='linkedin'], input[placeholder*='LinkedIn']")
                if await linkedin_input.count() > 0 and user.linkedin_url:
                    await linkedin_input.first.fill(user.linkedin_url)

                # Upload Resume
                resume_input = page.locator("input[type='file']")
                if await resume_input.count() > 0 and user.resume_file_path:
                    await resume_input.first.set_input_files(user.resume_file_path)
                    await asyncio.sleep(1.5)

                # Capture review screenshot
                await page.screenshot(path=screenshot_path, full_page=False)

                # Check submit button
                submit_btn = page.locator("button[type='submit'], input[type='submit'], button:has-text('Submit Application')")
                if await submit_btn.count() > 0 and auto_submit:
                    await submit_btn.first.click()
                    await asyncio.sleep(2)

                await browser.close()
                return {
                    "success": True,
                    "status": ApplyStatus.SUBMITTED.value,
                    "message": "ATS Application fields filled and submitted successfully!",
                    "screenshot_path": screenshot_path,
                    "apply_url": job.apply_url
                }

            except Exception as e:
                await page.screenshot(path=screenshot_path, full_page=False)
                await browser.close()
                return {
                    "success": False,
                    "status": ApplyStatus.FAILED.value,
                    "message": f"ATS Application error: {str(e)}",
                    "screenshot_path": screenshot_path,
                    "apply_url": job.apply_url
                }

apply_service = ApplyService()
