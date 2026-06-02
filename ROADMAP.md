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
- Shoot-first logging (new rolls open **Log frame note**; notes-only list + icon strip before scans)
- Rolls index (`/projects/rolls/`) with preview strip; rolls keep `owner` when project is deleted
- Header nav: **Projects** | **Rolls** (account menu for logout / delete only)
- Delete roll confirmation
- Required `Project.owner` and `FilmRoll.owner` (migration `0011_require_owner` with backfill)
- ngrok dev tunnel support (`ALLOWED_HOSTS`, `NGROK_ORIGIN` for CSRF) — see README

### Workflow testing (localhost) — passed

Full photographer flow verified on localhost:

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

**Edge case noted:** deleting a user removes owned projects (CASCADE); rolls linked only via M2M may remain until explicitly deleted — mitigated by `FilmRoll.owner` on create and on project delete.

---

## Next

### Image storage

- ~~Configure Cloudinary (`.env` + django-cloudinary-storage)~~ — done
- Verify upload, display, and deletion workflows on ngrok / production
- Optional: `python manage.py upload_local_scans` for legacy `media/` files

### External testing

- ~~Test application through ngrok~~ — basic mobile access verified
- Verify image uploads through Cloudinary (on ngrok / production)
- Test on desktop and mobile browsers (broader flows: import, delete, account)
- Test account creation and authentication outside localhost

### User testing

- Invite 1–2 photographers to use the application
- Observe workflow friction points
- Collect feedback
- Prioritize improvements

---

## Production deployment

**After** image storage and external testing are solid.

- Review Django security settings
- Configure environment variables and secrets
- Configure production media and static file settings
- Deploy to DigitalOcean
- Verify backups and recovery process

---

## Product improvements

- Rolls-first home page (rolls index + nav exist; optional default landing on Rolls)
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

Current focus: finish Cloudinary checks on ngrok, then deploy and invite real users. ngrok is for dev testing only (Mac must stay on).
