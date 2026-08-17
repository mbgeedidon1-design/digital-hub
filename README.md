# Digital Hub — Professional Edition

Digital Hub is a mobile-first digital services platform for photo editing, graphic design, websites/software, music/audio and digital downloads.

## Customer workflow

1. Customer opens **Send a Photo**.
2. Customer uploads an image and instructions.
3. The server creates a unique tracking link and request number.
4. The request appears in **Admin → Photo editing inbox**.
5. Admin downloads the original, edits it in a preferred editor, and uploads the result.
6. Customer opens the tracking link and downloads the completed file.

## Admin portal

`/admin`

- Photo editing inbox
- Original-file download
- Status updates: Received → Editing → Waiting for customer → Completed
- Finished-result upload
- Customer tracking link
- Customer orders
- Service management
- Digital product uploads

## AI customer assistant

The floating **Ask Digital Hub AI** assistant is included.

- Without an API key, it uses a safe built-in fallback response.
- With `OPENAI_API_KEY` configured in Render, it uses the OpenAI Responses API.
- `OPENAI_MODEL` defaults to `gpt-5.6`.

Keep the API key server-side as a Render environment variable. Never put it in browser JavaScript or commit it to GitHub.

## Important production storage note

The current Free Render web service uses its normal filesystem. That is suitable for testing the workflow, but customer uploads and digital products should not be treated as permanent production storage there. Before accepting real customer work, connect persistent/object storage (for example an object-storage provider) and store file metadata in PostgreSQL.

## Production upgrades recommended

- PostgreSQL database
- Persistent object storage for images/products
- M-Pesa checkout and payment verification
- WhatsApp/SMS/email notifications
- Customer accounts
- Admin audit log
- Rate limiting and upload scanning
- Privacy/terms pages
- Backups
- HTTPS/custom domain
- Image previews and thumbnails
- Paid digital-product checkout
