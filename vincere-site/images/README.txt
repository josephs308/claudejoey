PHOTOGRAPHY
===========
The site now loads photos directly from the Unsplash CDN - there are no image
files to upload. Every photo is served at 3840px wide (4K) with a responsive
srcset so phones pull a smaller file and only 4K screens pull the 4K version.

All ten are licensed "Free to use under the Unsplash License": commercial use
permitted, no attribution required, no account needed.

SLOT         PHOTOGRAPHER        SUBJECT
hero         Arlington Research  People working at desks in an open-plan office
about-team   Vitaly Gariev       Team working together in an open-plan office
stack-hero   1981 Digital        Marketing analytics dashboard
lsa          Berkeley Communications  Taking an inbound call at a desk
seo          1981 Digital        Search analytics dashboard
aeo          Aerps.com           Laptop showing an AI assistant response
websites     Marc Mueller        Front-end code in an editor (custom build, no CMS)
ppc          Stephen Phillips    Laptop showing Google search results
meta-ads     dlxmedia.hu         Social Media folder on a phone, Instagram and Facebook visible
branding     2H Media            Brand identity across laptop and phone

SWAPPING A PHOTO
Find the images.unsplash.com URL in the page and replace the photo ID (the
"photo-1686061593213-98dad7c599b9" part). Keep the query string - it is what
sets the 4K size and the crop.

SELF-HOSTING INSTEAD
If you would rather not depend on the Unsplash CDN, download each photo, export
at 3840x1612, compress to under ~600KB (squoosh.app), drop it in this folder,
and change the src back to images/<slot>.jpg. The fallback placeholder is still
wired in, so a missing file degrades gracefully instead of showing a broken icon.

SERVICE PAGE PHOTOS (3 per page, all topic-specific)
Branding  colour reference book / design books and brochures / identity on laptop+phone
Websites  code editor / monitor with live site / front-end code close-up
LSA       Google search on phone / Google homepage on phone / inbound call at a desk
SEO       Google results on screen / analytics dashboard close-up / ranking dashboard
AEO       ChatGPT conversation on phone / ChatGPT logo on phone / AI answer on laptop
PPC       Google search on phone / Google logo on screen / Google results on laptop
Meta Ads  shooting content on iPhone / camera ready for a shoot / Instagram+Facebook apps
