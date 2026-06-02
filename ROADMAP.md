# Frame Notes — Roadmap

Living plan for what’s shipped, what’s next, and what’s later.

---

## Shipped

- User accounts (sign up, login, logout, delete account)
- Per-user projects — list/detail/roll views scoped to `request.user` as owner
- Projects, film rolls, and frame notes
- Lab scan folder import
- Contact sheet view
- Lightbox viewing
- Favorites
- In-lightbox note editing (AJAX)

---

## Next

### Workflow testing (localhost)

Test the complete photographer workflow:

- Create account
- Create project
- Create roll
- Import scan folder
- Review contact sheet
- Favorite frames
- Add notes
- Edit notes
- Delete roll
- Delete project
- Delete account

Then:

- Document bugs and friction points
- Fix issues discovered during testing

**Edge cases to check:** deleting a user removes owned projects (CASCADE); rolls linked only via M2M may remain until explicitly deleted.

### Data / auth hardening

- Backfill `Project.owner` for any legacy null rows
- Migration to require `Project.owner` (`null=False`)

### Image storage

- Configure Cloudinary image storage
- Move scan uploads from local `media/` to cloud storage
- Verify upload, display, and deletion workflows

### External testing

- Test application through ngrok
- Verify image uploads through Cloudinary
- Test on desktop and mobile browsers
- Test account creation and authentication outside localhost

### User testing

- Invite 1–2 photographers to use the application
- Observe workflow friction points
- Collect feedback
- Prioritize improvements

---

## Production deployment

**After** image storage and workflow testing are solid.

- Review Django security settings
- Configure environment variables and secrets
- Configure production media and static file settings
- Deploy to DigitalOcean
- Verify backups and recovery process

---

## Product improvements

- Rolls-first home page
- Favorites filtering
- Search and filtering
- Archive workflow (`is_archived` exists on the model)
- Mobile-friendly contact sheet and forms

---

## Future exploration

- Darkroom print tracking
- Public contact sheet sharing
- PDF exports
- REST API endpoints
- Native iOS application
- Cleanup orphaned rolls when projects or accounts are deleted
- Optional `accounts/` URL prefix for auth routes

---

## Notes

Current focus: validate the full photographer workflow on localhost, then Cloudinary + external access, then deploy and invite real users. Expand the feature set after that.
