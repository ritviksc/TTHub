# Frontend issues

These are the frontend issues from the September review, written so they can be copied straight into GitBucket. Each issue has a title, a priority, a milestone, labels and a description. Copy the title into the issue title box, set the milestone and labels in GitBucket, and copy everything under "Description:" into the body.

Issues are grouped by milestone. Within each milestone they're sorted by priority, and issues that other work depends on come first.

Milestones:

Milestone 2 (ends Friday 18 September): most of the super admin pages, plus the shared pages they need. No LLM summaries and no ACC report.

Milestone 3 (two-week sprint): the LLM and ACC report work, and most of the remaining branch manager and instructor features. Ideally nearly everything is finished by the end of this milestone.

Milestone 4 (one-week sprint): checking and testing the whole project, fixing bugs and refining the UI. No new features.

Priority levels:

High: core features the client needs, or something other issues are waiting on.

Medium: the page exists or is planned, but it's missing features or still shows dummy data.

Low: we still need to decide whether this is worth building at all.

## Quick list

### Milestone 2

1. [High] Build a shared participant detail page for all three roles
2. [High] Build a shared user detail page for staff accounts
3. [High] Make one shared participants list and use it for all three roles
4. [Medium] Add photos for participants and staff
5. [Medium] Super admin Participants page: branch filter, photos and links to the detail page
6. [Medium] Super admin Users page: branch filter and links to the user detail page
7. [Medium] Branch detail page: add attendance and questionnaire stats
8. [Medium] Branch detail page: photos, links to detail pages and removing participants
9. [Medium] Build the super admin National overview page
10. [Medium] Decide how GP consent is stored and shown
11. [Low] Decide whether to keep the Administration page

### Milestone 3

12. [High] Build the branch manager Reports page (quarterly reports with LLM help)
13. [High] Build the super admin Reporting page (quarterly reports and ACC report)
14. [High] Let staff add comments on a participant from the participant detail page
15. [High] Session detail: change absence reasons to a dropdown with an Other text box
16. [High] Build the branch manager Sessions page by reusing the instructor session pages
17. [Medium] Add LLM summaries to the participant detail, user detail and National overview pages
18. [Medium] Create session form: remove session name and make activity a dropdown
19. [Medium] Branch manager Overview page: redesign and connect to real data
20. [Medium] Instructor Home page: connect to real data and tidy up
21. [Medium] Build the branch manager Instructors page
22. [Low] Decide whether sessions need scheduled start times
23. [Low] Decide whether to build or remove the Feedback pages

### Milestone 4

24. [High] Test every page for each role
25. [Medium] Tidy up the UI and make pages consistent

---

# Milestone 2

## 1. Build a shared participant detail page for all three roles

Priority: High

Milestone: Milestone 2

Labels:
- Common
- Super Admin

Description:
- We need one participant detail page that super admins, branch managers and instructors all use. Think of a contact card on your phone. The participant's photo goes in the top left with their name and basic details next to it, and their stats and staff comments go underneath.
- All three roles see pretty much the same page, so build it once. Don't make three copies. Put the page (or the main parts of it, as components) somewhere shared, then give each role a route that uses it. If one role needs to see slightly less, handle that with a prop or a role check inside the page.
- The page should show the participant's details, their attendance history, and how they're tracking over time, for example whether their strength is improving. That trend data could come from instructor comments or from the differences between their physical health reports. The LLM summary of the participant comes later in milestone 3 (issue 17), so don't build it here.
- A lot of other issues link to this page (the branch page, all the participants lists, session detail and comments), so it should be one of the first things we build.

---

## 2. Build a shared user detail page for staff accounts

Priority: High

Milestone: Milestone 2

Labels:
- Common
- Super Admin

Description:
- We need a page that shows one staff member: their details, their role and what they're allowed to do, and some stats. Super admins can view and edit branch managers and instructors. Branch managers use the same page but can only view and edit instructors in their own branch.
- As with the participant detail page, build one page and use role checks for what each role can do, instead of making two copies. Stats might be useful here too. Work out what's actually worth showing once the basic page works. Any LLM summary is covered in issue 17.
- The super admin Users page (issue 6) and the branch detail page (issue 8) both link here.

---

## 3. Make one shared participants list and use it for all three roles

Priority: High

Milestone: Milestone 2

Labels:
- Common
- Super Admin
- Branch Manager
- Instructor
- Backend

Description:
- The super admin Participants page works. The instructor Participants page needs replacing, and the branch manager one is still a Coming Soon placeholder (route bm-participants). Please don't copy the super admin page into the other two folders. Move the list part (table, search and filters) into a component under frontend/src/components/participants/ and use that component on all three pages.
- The only real difference between the roles is which participants they can see. Super admins see everyone. Branch managers and instructors only see participants in their own branch, so they don't need a branch filter. Check that the backend only sends back that branch's participants for those roles. Hiding the extra rows in the frontend isn't enough.
- Clicking a participant should open the participant detail page (issue 1).

---

## 4. Add photos for participants and staff

Priority: Medium

Milestone: Milestone 2

Labels:
- Common
- Backend

Description:
- Several pages need a person's photo to the left of their name: the branch detail page, the participants lists, the Users page and both detail pages. The frontend doesn't show photos yet, which is why dashboard.css has an initials-avatar class as a stand-in.
- Backend support should support photos storing now but needs to be checked
- On the frontend, add a way to upload a participant photo (with the consent checkbox and date), and one shared avatar component that shows the photo or falls back to initials when there isn't one. The other issues can then just use that component.
- Staff accounts don't have a photo field yet. Decide whether staff need photos, and if so, add that on the backend too.

---

## 5. Super admin Participants page: branch filter, photos and links to the detail page

Priority: Medium

Milestone: Milestone 2

Labels:
- Super Admin

Description:
- The super admin Participants page needs three changes. Add a filter so you can pick a branch and only see its participants. Show each participant's photo to the left of their name. Clicking a participant should take you to their participant detail page.
- Make these changes inside the shared participants list component from issue 3, so branch managers and instructors get the photos and links too. Photos depend on issue 4.

---

## 6. Super admin Users page: branch filter and links to the user detail page

Priority: Medium

Milestone: Milestone 2

Labels:
- Super Admin

Description:
- The super admin Users page needs a filter so you can see staff from one branch at a time. Clicking a user's name should take you to their user detail page (issue 2).

---

## 7. Branch detail page: add attendance and questionnaire stats

Priority: Medium

Milestone: Milestone 2

Labels:
- Super Admin

Description:
- The Branches page mostly works. When you click into a branch (frontend/src/views/SuperAdmin/BranchDetail.vue), the details section still needs attendance stats and questionnaire stats for that branch. Use the existing stat-grid and stat-tile classes in dashboard.css for these.

---

## 8. Branch detail page: photos, links to detail pages and removing participants

Priority: Medium

Milestone: Milestone 2

Labels:
- Super Admin

Description:
- On the branch detail page, branch managers, instructors and participants should each show a photo to the left of their name (see issue 4). Hovering over a name should show it's clickable, and clicking should go to the right page: the user detail page for staff and the participant detail page for participants.
- Super admins also need to be able to remove a participant from this page. Decide first what "remove" means here. apis.js already has a deactivateParticipant function, so that might be enough.

---

## 9. Build the super admin National overview page

Priority: Medium

Milestone: Milestone 2

Labels:
- Super Admin

Description:
- The National overview page is a Coming Soon placeholder (route sa-overview). It should show stats for every branch and how each branch is performing. The LLM summary of these stats comes later in milestone 3 (issue 17), so leave room for it but don't build it here.
- Prototype: docs/prototypes/Super Admin/Super Admin - Page 1 (National Overview).png.

---

## 10. Decide how GP consent is stored and shown

Priority: Medium

Milestone: Milestone 2

Labels:
- Common
- Backend

Description:
- GP consent needs to be looked at across the instructor, branch manager and super admin pages. We need to decide which record it's attached to, who can see it, who can change it, and where it shows up in the app. One option is to show it on the relevant detail page.
- Write the decision in this issue before anyone starts building, because it affects the detail pages (issues 1 and 2).

---

## 11. Decide whether to keep the Administration page

Priority: Low

Milestone: Milestone 2

Labels:
- Super Admin

Description:
- The prototype for the super admin Administration page includes vocabularies, an audit log and exports. Work out whether these are in scope, whether they'd actually be useful, and whether they're easy to build. If the answer is mostly no, remove the page, its route and its nav link.
- Prototype: docs/prototypes/Super Admin/Super Admin - Page 5 (Adminstration).png.

---

# Milestone 3

## 12. Build the branch manager Reports page (quarterly reports with LLM help)

Priority: High

Milestone: Milestone 3

Labels:
- Branch Manager
- Backend

Description:
- Branch managers need to write a quarterly report and send it to the super admin. Right now the page is a Coming Soon placeholder (route bm-reports). Start from the prototype in docs/prototypes/Branch Manager/Branch Manager - Page 6 (Reports).png.
- The LLM should help the manager write the report. One way to do this is to have it draft sections from the branch's attendance and participant data, which the manager then checks and edits. We'll need to try a few versions of this before it feels right, so expect some back and forth.
- The super admin Reporting page (issue 13) reads these reports. Agree on how a report is stored in the backend before building either page, so the two pages fit together.

---

## 13. Build the super admin Reporting page (quarterly reports and ACC report)

Priority: High

Milestone: Milestone 3

Labels:
- Super Admin
- Backend

Description:
- This is one of the biggest jobs left on the frontend. The page is currently a Coming Soon placeholder (route sa-reporting). Start from the prototype in docs/prototypes/Super Admin/Super Admin - Page 3 (Reporting).png.
- The page needs to do two things. It shows every quarterly report the branch managers have sent in, and it helps the super admin fill out the ACC report. As much of the ACC report as possible should be filled in automatically, using the LLM to summarise the branch data and the quarterly reports.
- This depends on the branch manager Reports page (issue 12). Whoever picks this up should probably split it into smaller issues, for example one for the list of quarterly reports and one for the ACC report.

---

## 14. Let staff add comments on a participant from the participant detail page

Priority: High

Milestone: Milestone 3

Labels:
- Common
- Instructor
- Backend

Description:
- Instructors need to be able to write notes about a participant, both during a session and outside of one. We've decided to keep this simple for now. Comments live on the participant detail page and are not linked to a session.
- If an instructor wants to leave a comment during a session, they click the participant's name on the session detail page. That takes them to the participant detail page, where they write the comment. This also lets them check the participant's stats while they're there, for example to see why someone hasn't come in for three weeks.
- Each comment should save who wrote it and when, and show the author's name. Super admins can see comments from every instructor and branch manager and can add their own. Branch managers and instructors get the same comment section.
- Attendance mode does not get any of this. Leave it as it is.
- This needs a comment model and endpoints on the backend, plus matching functions in frontend/src/apis.js. It depends on issue 1. We might add session-linked comments later, but plain comments come first.

---

## 15. Session detail: change absence reasons to a dropdown with an Other text box

Priority: High

Milestone: Milestone 3

Labels:
- Instructor
- Backend

Description:
- The client is interested in why people miss sessions, so we want better absence data. On the session detail page, a participant's status should only be Present or Absent. The code currently also has an Excused status (ATTENDANCE_STATUSES in frontend/src/utils/sessions.js), and that should be removed.
- When someone is marked Absent, show a dropdown of reasons. We still need to settle the final list, but it should be along the lines of No show, Medical appointment, Transport issue and Other. If the instructor picks Other, show a text box so they can type the reason, if they know it.
- Things to update: the reason list in utils/sessions.js, the session detail page, anything that counts statuses (such as countByStatus), and the backend field for absence reasons so typed-in reasons get saved.

---

## 16. Build the branch manager Sessions page by reusing the instructor session pages

Priority: High

Milestone: Milestone 3

Labels:
- Branch Manager

Description:
- The branch manager Sessions page is a Coming Soon placeholder (route bm-sessions). Instructors already have working Sessions, Session detail and Attendance mode pages in frontend/src/views/Instructor/. Branch managers need the same pages under their own routes.
- Don't copy the files. Move the parts both roles use into components (CreateSessionModal in components/sessions/ already works this way), then make small page files for each role that use them. Add the new routes to frontend/src/router/index.js with the branch manager role.
- Prototype: docs/prototypes/Branch Manager/Branch Manager - Page 2 (Sessions).png.

---

## 17. Add LLM summaries to the participant detail, user detail and National overview pages

Priority: Medium

Milestone: Milestone 3

Labels:
- Common
- Super Admin
- Backend

Description:
- In milestone 2 we build the participant detail page (issue 1), the user detail page (issue 2) and the National overview page (issue 9) without any LLM features. This issue adds the LLM summaries to those pages.
- Participant detail: a short summary of the participant, such as their attendance and how they're tracking over time.
- User detail: check whether a summary is actually useful for staff before building it.
- National overview: a paragraph-long summary of the stats for every branch.
- The branch manager Reports page (issue 12), the super admin Reporting page (issue 13) and the branch manager Overview page (issue 19) also use the LLM, so agree on one way of calling it from the backend and reuse it.

---

## 18. Create session form: remove session name and make activity a dropdown

Priority: Medium

Milestone: Milestone 3

Labels:
- Instructor
- Backend

Description:
- The Create session form (frontend/src/components/sessions/CreateSessionModal.vue) asks for a session name, and I don't think it's needed. Most sessions repeat every week, so they'd all be called something like "Thursday morning class". Asking for a name suggests every session needs a unique one, which is confusing. The date and time are enough to tell sessions apart.
- Activity is currently a free text box. Change it to a dropdown with a short, fixed list. The options still need to be decided, but likely ones are Standard strength and mobility training and Fitness test.
- This affects the modal, the Sessions list (its first column shows the session name), and the session model and API on the backend.

---

## 19. Branch manager Overview page: redesign and connect to real data

Priority: Medium

Milestone: Milestone 3

Labels:
- Branch Manager
- Backend

Description:
- The branch manager Overview page (frontend/src/views/BranchManager/Overview.vue) only shows dummy placeholder data. It needs a full redesign and has to be wired up to the backend. It should show real stats for the branch and an LLM summary of how the branch is doing.
- Prototype: docs/prototypes/Branch Manager/Branch Manager - Page 1 (Overview).png. Remove the placeholder data and any code that only existed to support it.

---

## 20. Instructor Home page: connect to real data and tidy up

Priority: Medium

Milestone: Milestone 3

Labels:
- Instructor
- Backend

Description:
- The instructor Home page (frontend/src/views/Instructor/Home.vue) is entirely dummy data. The layout is pretty good, but it needs some redesign and has to be connected to the backend.
- Specific changes: rename the "Start roll call" button to "Start session", and remove the open session details section.
- The page also assumes sessions have scheduled start times, which we don't think the backend supports. Issue 22 covers whether to add that. Until it's decided, don't build anything that relies on start times.

---

## 21. Build the branch manager Instructors page

Priority: Medium

Milestone: Milestone 3

Labels:
- Branch Manager

Description:
- The branch manager Instructors page is a Coming Soon placeholder (route bm-instructors). It's similar to the instructors section of the super admin branch detail page. The main difference is that branch managers can only add instructors, so this page probably needs its own design rather than a reuse of the super admin one.
- Check whether the existing CreateInstructor.vue page (route create-instructor) can be reused for adding instructors. Clicking an instructor should open the user detail page (issue 2).
- Prototype: docs/prototypes/Branch Manager/Branch Manager - Page 4 (Instructors).png.

---

## 22. Decide whether sessions need scheduled start times

Priority: Low

Milestone: Milestone 3

Labels:
- Instructor
- Backend

Description:
- The instructor Home page assumes each session has a scheduled start time. We don't think the backend supports this yet. Decide whether scheduled start times are worth adding and whether it's realistic in the time we have.
- If yes, create an issue for the backend change. If no, remove anything on the Home page that relies on start times.

---

## 23. Decide whether to build or remove the Feedback pages

Priority: Low

Milestone: Milestone 3

Labels:
- Branch Manager
- Instructor

Description:
- Branch managers and instructors both have a Feedback page that's currently a Coming Soon placeholder (routes bm-feedback and in-feedback). Look at the prototypes and decide whether these pages would actually be useful and whether we can build them properly.
- If we keep them, create issues to build them. If not, remove the routes and the nav links.
- Prototypes: docs/prototypes/Branch Manager/Branch Manager - Page 5 (Feedback).png and docs/prototypes/Instructor/Instructor - Page 4 (Feedback).png.

---

# Milestone 4

## 24. Test every page for each role

Priority: High

Milestone: Milestone 4

Labels:
- Common
- Super Admin
- Branch Manager
- Instructor
- Backend

Description:
- Milestone 4 is for checking and testing the whole project, so no new features should be started in this milestone.
- Log in as a super admin, a branch manager and an instructor, and go through every page for that role. Check that each page loads real data, and that creating, editing and deleting things works. The seed_test_data command (docs/backend/seed_test_data.md) gives you test data to work with.
- Check that each role can only see and change what it's allowed to, for example that branch managers and instructors only see their own branch. Check the backend blocks this too, not just the frontend.
- Create a separate issue for each bug you find so it can be tracked and fixed during the sprint.

---

## 25. Tidy up the UI and make pages consistent

Priority: Medium

Milestone: Milestone 4

Labels:
- Common
- Super Admin
- Branch Manager
- Instructor

Description:
- Go through the app and make the pages look and behave the same way: spacing, buttons, tables, headings, loading states and error messages. Use docs/frontend/frontend-conventions.md as the reference.
- Remove any leftover placeholder data, Coming Soon pages we decided not to build, and unused CSS or components.
- Check the pages work at the screen sizes people will actually use, for example a tablet if that's what instructors use during sessions.
