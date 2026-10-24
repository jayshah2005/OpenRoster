# Source audit report

Generated 2026-10-24 16:36 UTC by `openroster audit --all`. A source runs only when its verdict is **allowed** and the owner set `reviewed: true`.

Summary: allowed: 153, blocked: 24, unknown: 1

## Known verdicts (always enforced in code)

| Hosts | Verdict | Reason |
|---|---|---|
| devpost.com | **blocked** | Terms of service forbid scraping and crawling. Hackathons hosted there enter through submissions or the hackathon's own site. |
| mlh.io, mlh.com | **permission_required** | Terms limit content to personal, non-commercial use and forbid republishing without written consent. |
| eventbrite.com, eventbrite.ca, eventbrite.co.uk | **blocked** | Terms forbid scraping. |
| linkedin.com | **blocked** | Terms forbid scraping; content requires login. |
| joinhandshake.com | **blocked** | Requires login; terms forbid automated access. |
| lu.ma, luma.com | **blocked** | Only official iCal subscription links may be used; unofficial JSON endpoints and pages are never fetched. |
| api.lu.ma | **allowed** | Official Luma iCal subscription export only. |
| docs.google.com, forms.gle, forms.office.com, tally.so, typeform.com, jotform.com, form.jotform.com | **link_only** | Form hosts: link to them, never fetch or submit. |
| calendar.google.com | **blocked** | Google's robots.txt disallows /calendar/ical/ for automated clients (found by the 2026-10-24 audit). Club Google Calendars can still be submitted event by event. |
| gdg.community.dev | **blocked** | robots.txt disallows /api/; event pages are rendered from that API. |

## Configured sources and hackathons

| ID | Source | Verdict | robots.txt | Terms | Terms flags | Platform | Reviewed | Checked |
|---|---|---|---|---|---|---|---|---|
| `bmo-student-events` | [BMO student events (on-campus and in-office)](https://jobs.bmo.com/ca/en/student-events) | **allowed** | allowed | - | - | html | yes | 2026-10-24 |
| `scotiabank-campus-events` | [Scotiabank campus events](https://www.scotiabank.com/careers/en/careers/campus-events.html) | **allowed** | allowed | [terms](https://www.scotiabank.com/ca/en/about/contact-us/legal.html) | terms: republishing | html | yes | 2026-10-24 |
| `scotiabank-jobs-student-programs` | [Scotiabank jobs site - student hackathon / competition postings (SHACKS, Canada's Top Students)](https://jobs.scotiabank.com/search/?q=student) | **allowed** | allowed | - | - | html | yes | 2026-10-24 |
| `rbc-students-graduates` | [RBC Careers - Students & Graduates (Campus events anchor)](https://jobs.rbc.com/ca/en/students-graduates) | **allowed** | allowed | [terms](http://www.rbc.com/legal/) | - | html_no_dates | yes | 2026-10-24 |
| `cibc-student-campus-events` | [CIBC - Student and campus events](https://www.cibc.com/en/about-cibc/careers/students-and-graduates/student-and-campus-events.html) | **allowed** | allowed | [terms](https://www.cibc.com/en/legal/legal-trademarks.html) | - | html_no_dates | yes | 2026-10-24 |
| `kpmg-ca-student-programs` | [KPMG Canada - Student programs (Ace the Case, Experience a Day)](https://kpmg.com/ca/en/careers/students/student-programs.html) | **allowed** | allowed | [terms](https://kpmg.com/ca/en/misc/legal.html) | terms: republishing | html_no_dates | yes | 2026-10-24 |
| `bain-toronto-students` | [Bain & Company - University of Toronto students page (programs + events)](https://www.bain.com/careers/work-with-us/students/toronto/) | **allowed** | allowed | [terms](https://www.bain.com/about/terms/) | terms: republishing | html | yes | 2026-10-24 |
| `bcg-on-campus-toronto` | [BCG Careers - On-campus page, University of Toronto (and other Canadian schools)](https://careers.bcg.com/global/en/on-campus/university-of-toronto) | **blocked** | allowed | [terms](https://www.bcg.com/about/terms-of-use) | terms: automated access, terms: republishing | html_no_dates | no | 2026-10-24 |
| `janestreet-programs-events` | [Jane Street - Programs and Events](https://www.janestreet.com/join-jane-street/programs-and-events/) | **allowed** | allowed | - | - | html_no_dates | yes | 2026-10-24 |
| `optiver-recruitment-events` | [Optiver - Recruitment events](https://optiver.com/recruitment-events/) | **allowed** | allowed | - | - | html | yes | 2026-10-24 |
| `imc-prosperity` | [IMC Prosperity - global student trading/algorithmic challenge](https://www.imc.com/us/corporate-news/prosperity-4) | **allowed** | allowed | [terms](https://www.imc.com/us/terms-conditions) | - | html | yes | 2026-10-24 |
| `twosigma-new-seekers-summit` | [Two Sigma - New Seekers Summit (1st/2nd-year undergrads)](https://www.twosigma.com/new-seekers-summit/) | **blocked** | allowed | [terms](https://www.twosigma.com/legal-disclosures/?entity=two-sigma-investments-lp&disclosure=legal-disclosure) | terms: automated access, terms: republishing | html_no_dates | no | 2026-10-24 |
| `bmo-virtual-workshops` | [BMO virtual student workshops](https://jobs.bmo.com/ca/en/student-events) | **allowed** | allowed | - | - | html | yes | 2026-10-24 |
| `hackclub-hackathons-api-upcoming` | [Hack Club Hackathons API (upcoming events)](https://hackathons.hackclub.com/api/events/upcoming) | **allowed** | no_robots | - | - | html_no_dates | yes | 2026-10-24 |
| `vector-institute-events` | [Vector Institute events (The Events Calendar REST)](https://vectorinstitute.ai/wp-json/tribe/events/v1/events) | **allowed** | allowed | - | - | html | yes | 2026-10-24 |
| `luma-canadian-undergraduate-technology-conference-cutc` | [Canadian Undergraduate Technology Conference (CUTC) (Luma iCal)](https://api.lu.ma/ics/get?entity=calendar&id=cal-oYQx6BHc1owy2ip) | **allowed** | allowed | - | - | html_no_dates | yes | 2026-10-24 |
| `luma-toronto-tech-week` | [Toronto Tech Week (Luma iCal)](https://api.lu.ma/ics/get?entity=calendar&id=cal-DdUEFsYsDVh7osG) | **allowed** | allowed | - | - | html | yes | 2026-10-24 |
| `luma-techto` | [TechTO (Luma iCal)](https://api.lu.ma/ics/get?entity=calendar&id=cal-NFIKWffXs4kAUi3) | **allowed** | allowed | - | - | html | yes | 2026-10-24 |
| `luma-torontoai` | [TorontoAI (Luma iCal)](https://api.lu.ma/ics/get?entity=calendar&id=cal-05jPeXeBQT1g9n3) | **allowed** | allowed | - | - | html_no_dates | yes | 2026-10-24 |
| `luma-waterloo-tech-adjacent-events` | [Waterloo Tech (+adjacent) Events (Luma iCal)](https://api.lu.ma/ics/get?entity=calendar&id=cal-rJoHBmPlHGvg5F8) | **allowed** | allowed | - | - | html_no_dates | yes | 2026-10-24 |
| `luma-waterloo-tech-week` | [Waterloo Tech Week (Luma iCal)](https://api.lu.ma/ics/get?entity=calendar&id=cal-N301eCjDJFPPHxA) | **allowed** | allowed | - | - | html_no_dates | yes | 2026-10-24 |
| `luma-socratica` | [Socratica (Luma iCal)](https://api.lu.ma/ics/get?entity=calendar&id=cal-cBMgU2QXqXZQSv1) | **allowed** | allowed | - | - | html_no_dates | yes | 2026-10-24 |
| `luma-ottawa-tech-thursday` | [Ottawa Tech Thursday (Luma iCal)](https://api.lu.ma/ics/get?entity=calendar&id=cal-yiYZCjVML6OJg7I) | **allowed** | allowed | - | - | html_no_dates | yes | 2026-10-24 |
| `luma-careerin-tech-society` | [Careerin Tech Society (Luma iCal)](https://api.lu.ma/ics/get?entity=calendar&id=cal-gUADv2P40s4rWOB) | **allowed** | allowed | - | - | html | yes | 2026-10-24 |
| `luma-tech2step-events` | [Tech2Step Events (Luma iCal)](https://api.lu.ma/ics/get?entity=calendar&id=cal-W6q2oD1np3YfMjq) | **allowed** | allowed | - | - | html_no_dates | yes | 2026-10-24 |
| `luma-tech-walk-and-talk-montreal` | [Tech Walk and Talk (Montreal) (Luma iCal)](https://api.lu.ma/ics/get?entity=calendar&id=cal-HL5D5MWKDM5EIX7) | **allowed** | allowed | - | - | html_no_dates | yes | 2026-10-24 |
| `uoft-engineering-events` | [U of T Faculty of Applied Science & Engineering events](https://www.engineering.utoronto.ca/wp-json/tribe/events/v1/events) | **allowed** | allowed | - | - | tribe | yes | 2026-10-24 |
| `uoft-engineering-undergrad-events` | [U of T Engineering undergraduate events (incl. PEY Co-op)](https://undergrad.engineering.utoronto.ca/wp-json/tribe/events/v1/events) | **allowed** | allowed | - | - | html | yes | 2026-10-24 |
| `uoft-sop-events` | [U of T Student Organization Portal (Resource Finder) events](https://sop.utoronto.ca/wp-json/tribe/events/v1/events) | **allowed** | allowed | - | - | html | yes | 2026-10-24 |
| `uoft-utm-events` | [UTM events listing](https://www.utm.utoronto.ca/events) | **allowed** | allowed | - | - | html | yes | 2026-10-24 |
| `uoft-utsc-cms-events` | [UTSC Computer & Mathematical Sciences department events](https://utsc.utoronto.ca/cms/events) | **allowed** | allowed | - | - | html_no_dates | yes | 2026-10-24 |
| `uoft-central-events` | [U of T central events aggregator](https://www.utoronto.ca/events) | **allowed** | allowed | - | - | html | yes | 2026-10-24 |
| `tmu-cs-seminar-calendar` | [TMU Computer Science student seminar calendar (Google Calendar)](https://calendar.google.com/calendar/ical/ryerson.ca_1889os4nvg1iujhlil4onene40e9k%40resource.calendar.google.com/public/basic.ics) | **blocked** | not_checked | - | - | unknown | no | 2026-10-24 |
| `dmz-flagship-events` | [DMZ (TMU) flagship events and programs](https://dmz.torontomu.ca/) | **allowed** | allowed | [terms](https://dmz.torontomu.ca/dmz-slsc) | - | html | yes | 2026-10-24 |
| `gdg-toronto` | [Google Developer Groups Toronto (GDG Toronto)](https://gdg.community.dev/gdg-toronto/) | **blocked** | not_checked | - | - | unknown | no | 2026-10-24 |
| `gdg-on-campus-tmu` | [GDG on Campus Toronto Metropolitan University](https://gdg.community.dev/gdg-on-campus-toronto-metropolitan-university-toronto-canada/) | **blocked** | not_checked | - | - | unknown | no | 2026-10-24 |
| `yorku-yuconnect-ical` | [YU Connect (CampusGroups) all public club events iCal](https://yuconnect.yorku.ca/ical/yorku/ical_yorku.ics) | **allowed** | allowed | - | - | html | yes | 2026-10-24 |
| `yorku-lassonde-events` | [Lassonde School of Engineering events (incl. EECS)](https://lassonde.yorku.ca/events/) | **allowed** | allowed | [terms](https://www.yorku.ca/about/privacy-legal/) | terms: republishing | ics | yes | 2026-10-24 |
| `ocadu-events` | [OCAD University events and exhibitions](https://www.ocadu.ca/events) | **allowed** | allowed | - | - | html | yes | 2026-10-24 |
| `ontariotechu-events` | [Ontario Tech University events calendar](https://events.ontariotechu.ca/) | **allowed** | no_robots | - | - | js_only | yes | 2026-10-24 |
| `seneca-mynews` | [Seneca student portal MyNews (Axero)](https://students.senecapolytechnic.ca/spaces/112/mynews/home) | **allowed** | allowed | - | - | html | yes | 2026-10-24 |
| `seneca-future-students-events` | [Seneca future students events and webinars](https://www.senecapolytechnic.ca/futurestudents/events-and-webinars.html) | **allowed** | allowed | - | - | html | yes | 2026-10-24 |
| `centennial-ieee-branch` | [IEEE Centennial College Student Branch events](https://edu.ieee.org/ca-centennial-college/calendar) | **allowed** | allowed | [terms](http://www.ieee.org/site_terms_conditions.html) | - | html | yes | 2026-10-24 |
| `georgebrown-sagbc-events` | [Student Association of George Brown College events](https://studentassociation.ca/events) | **allowed** | allowed | [terms](https://www.studentassociation.ca/legal/) | - | html_no_dates | yes | 2026-10-24 |
| `durham-events` | [Durham College events calendar](https://durhamcollege.ca/wp-json/tribe/events/v1/events?categories=academic) | **allowed** | allowed | - | - | html_no_dates | yes | 2026-10-24 |
| `techto-events` | [TechTO events](https://techto.org/events) | **allowed** | allowed | [terms](https://docs.google.com/document/d/e/2PACX-1vQd_C_Nt9pwEy5bLQ075wA0QfHpXD922eHMN659rUTw32wK-IckCGhFisWCMI0W2a-Pq8gSd8YxEw4N/pub) | - | html | yes | 2026-10-24 |
| `brock-busu-events` | [Brock University Students' Union (BUSU) events](https://www.brockbusu.ca/whats-on/events/) | **allowed** | allowed | - | - | html_no_dates | yes | 2026-10-24 |
| `brock-csc-site` | [Brock Computer Science Club website](https://brockcsc.ca/events) | **allowed** | allowed | - | - | html_no_dates | yes | 2026-10-24 |
| `brock-linc-events` | [Brock LINC (Generator at One successor) entrepreneurship events](https://brocku.ca/linc/entrepreneurship-events/) | **allowed** | allowed | - | - | html_no_dates | yes | 2026-10-24 |
| `niagara-college-events` | [Niagara College events calendar (The Events Calendar)](https://www.niagaracollege.ca/events/list/) | **allowed** | allowed | [terms](https://www.niagaracollege.ca/disclaimer/) | terms: republishing | jsonld | yes | 2026-10-24 |
| `innovate-niagara-events` | [Innovate Niagara tech events](https://www.innovateniagara.com/site/tech-events-niagara) | **allowed** | allowed | - | - | html | yes | 2026-10-24 |
| `mcmaster-news-events-ics` | [McMaster University central events (news.mcmaster.ca, Events Manager)](https://news.mcmaster.ca/events.ics) | **allowed** | allowed | - | - | html_no_dates | yes | 2026-10-24 |
| `mcmaster-engineering-events` | [McMaster Faculty of Engineering events (incl. Computing and Software)](https://www.eng.mcmaster.ca/about-us/events/) | **allowed** | allowed | [terms](https://www.mcmaster.ca/opr/html/footer/main/terms_of_use.html) | terms: republishing | html | yes | 2026-10-24 |
| `mcmaster-gdg-on-campus` | [GDG on Campus McMaster University (Bevy chapter page)](https://gdg.community.dev/gdg-on-campus-mcmaster-university-hamilton-canada/) | **blocked** | not_checked | - | - | unknown | no | 2026-10-24 |
| `msu-mcmaster-events` | [McMaster Students Union clubs events calendar](https://msumcmaster.ca/clubs/events-calendar/) | **allowed** | allowed | [terms](https://msumcmaster.ca/terms-conditions-of-use/) | terms: republishing | html_no_dates | yes | 2026-10-24 |
| `mohawk-events` | [Mohawk College events](https://www.mohawkcollege.ca/events) | **allowed** | allowed | [terms](https://www.mohawkcollege.ca/faq/program-disclaimer) | - | html | yes | 2026-10-24 |
| `mohawk-msa-events` | [Mohawk Students' Association events](https://mohawkstudents.ca/get-involved/events/) | **allowed** | allowed | [terms](https://mohawkstudents.ca/supports/legal-counselling/) | - | html | yes | 2026-10-24 |
| `innovation-factory-events` | [Innovation Factory (Hamilton) events calendar](https://www.innovationfactory.ca/events/) | **allowed** | allowed | [terms](https://innovationfactory.ca/events/legal-ip-mentorship-office-hours-with-robinson-banwatt-law/) | - | jsonld | yes | 2026-10-24 |
| `sheridan-ssu-events` | [Sheridan Student Union events](https://www.thessu.ca/events) | **allowed** | allowed | [terms](https://www.thessu.ca/graduation-photos) | - | ics | yes | 2026-10-24 |
| `sheridan-gdg-on-campus` | [GDG on Campus Sheridan College (Bevy chapter page)](https://gdg.community.dev/gdg-on-campus-sheridan-college-trafalgar-road-campus-oakville-canada/) | **blocked** | not_checked | - | - | unknown | no | 2026-10-24 |
| `uwaterloo-central-events-ics` | [University of Waterloo central events calendar (WCMS iCal)](https://uwaterloo.ca/events/events/ical) | **allowed** | no_robots | - | - | html | yes | 2026-10-24 |
| `uwaterloo-cs-events-ics` | [Cheriton School of Computer Science events (iCal)](https://cs.uwaterloo.ca/events/ical) | **allowed** | allowed | - | - | html_no_dates | yes | 2026-10-24 |
| `uwaterloo-engineering-events-ics` | [Waterloo Engineering events (iCal)](https://uwaterloo.ca/engineering/events/ical) | **allowed** | no_robots | - | - | html_no_dates | yes | 2026-10-24 |
| `uwaterloo-wics-events-ics` | [Waterloo Women in Computer Science events (iCal)](https://uwaterloo.ca/women-in-computer-science/events/ical) | **allowed** | no_robots | - | - | html | yes | 2026-10-24 |
| `uwaterloo-csclub-ics` | [UW Computer Science Club events (iCal)](https://csclub.uwaterloo.ca/events.ics) | **allowed** | no_robots | - | - | html | yes | 2026-10-24 |
| `wusa-events-tribe` | [Waterloo Undergraduate Student Association (WUSA) events incl. clubs](https://wusa.ca/wp-json/tribe/events/v1/events) | **blocked** | no_robots | - | - | unknown | yes | 2026-10-24 |
| `velocity-events` | [Velocity (UW) events](https://www.velocityincubator.com/events) | **allowed** | allowed | - | - | html | yes | 2026-10-24 |
| `accelerator-centre-tribe` | [Accelerator Centre (Waterloo) events](https://www.acceleratorcentre.com/wp-json/tribe/events/v1/events) | **allowed** | allowed | - | - | html_no_dates | yes | 2026-10-24 |
| `laurier-events-ics` | [Wilfrid Laurier University events calendar (iCal)](https://events.wlu.ca/_data/current.ics) | **allowed** | no_robots | - | - | html | yes | 2026-10-24 |
| `laurier-gdg-on-campus` | [GDG on Campus Wilfrid Laurier University (Bevy chapter page)](https://gdg.community.dev/gdg-on-campus-wilfrid-laurier-university-waterloo-canada/) | **blocked** | not_checked | - | - | unknown | no | 2026-10-24 |
| `uoguelph-news-events-tribe` | [University of Guelph central events (news.uoguelph.ca, The Events Calendar)](https://news.uoguelph.ca/wp-json/tribe/events/v1/events) | **allowed** | allowed | - | - | html | yes | 2026-10-24 |
| `uoguelph-gryphlife-campusgroups-ics` | [University of Guelph GryphLife (CampusGroups) public iCal](https://uoguelph.campusgroups.com/ical/uoguelph/ical_uoguelph.ics) | **allowed** | allowed | - | - | html | yes | 2026-10-24 |
| `uoguelph-computing-events` | [Guelph School of Computer Science / CCMPS events](https://www.uoguelph.ca/computing/events) | **allowed** | allowed | [terms](https://www.uoguelph.ca/web/terms/) | - | html | yes | 2026-10-24 |
| `conestoga-events` | [Conestoga College events](https://blogs1.conestogac.on.ca/events) | **allowed** | allowed | [terms](https://www.conestogac.on.ca/admissions/registrar-office/terms-definitions) | - | html | yes | 2026-10-24 |
| `conestoga-csi-events` | [Conestoga Students Inc. (CSI) events](https://www.conestogastudents.com/getinvolved/eventslist/) | **allowed** | allowed | [terms](https://mygradphotosconestoga.com/) | - | html | yes | 2026-10-24 |
| `conestoga-gdg-on-campus` | [GDG on Campus Conestoga College (Bevy chapter page)](https://gdg.community.dev/gdg-on-campus-conestoga-college-waterloo-campus-waterloo-canada/) | **blocked** | not_checked | - | - | unknown | no | 2026-10-24 |
| `uoguelph-gdg-on-campus` | [GDG on Campus University of Guelph (Bevy chapter page)](https://gdg.community.dev/gdg-on-campus-university-of-guelph-guelph-canada/) | **blocked** | not_checked | - | - | unknown | no | 2026-10-24 |
| `western-events-ics` | [Western University events calendar (iCal)](https://www.uwo.ca/events/_data/current.ics) | **allowed** | allowed | - | - | html | yes | 2026-10-24 |
| `western-career-events` | [Western Career Education events & workshops](https://career.uwo.ca/take_action/events_workshops/index.html) | **allowed** | allowed | [terms](https://www.uwo.ca/vpfinance/legalcounsel/privacy/) | - | html | yes | 2026-10-24 |
| `western-csd-news` | [Western Computer Science department news](https://www.csd.uwo.ca/news/) | **allowed** | no_robots | [terms](https://www.uwo.ca/vpfinance/legalcounsel/privacy/) | - | html | yes | 2026-10-24 |
| `fsu-events-ics` | [Fanshawe Student Union events calendar (iCal)](https://www.fsu.ca/fsucalendar.ics) | **allowed** | no_robots | - | - | html | yes | 2026-10-24 |
| `fanshawe-career-services-events` | [Fanshawe Career Services events & workshops](https://www.fanshawec.ca/students/support/employment/career-services/events-workshops) | **allowed** | allowed | - | - | html_no_dates | yes | 2026-10-24 |
| `uwindsor-cs-event-calendar` | [UWindsor School of Computer Science event calendar](https://www.uwindsor.ca/science/computerscience/event-calendar) | **allowed** | allowed | [terms](https://www.uwindsor.ca/394207/terms-and-conditions) | - | ics | yes | 2026-10-24 |
| `uwindsor-event-calendar` | [University of Windsor main event calendar](https://www.uwindsor.ca/event-calendar) | **allowed** | allowed | [terms](https://www.uwindsor.ca/394207/terms-and-conditions) | - | html | yes | 2026-10-24 |
| `uwindsor-css-events` | [UWindsor Computer Science Society events](https://css.uwindsor.ca/events) | **allowed** | allowed | - | - | html | yes | 2026-10-24 |
| `stclair-career-fairs` | [St. Clair College career fairs & industry events](https://stclaircollege.ca/career-fairs) | **allowed** | allowed | - | - | html_no_dates | yes | 2026-10-24 |
| `queens-computing-calendar-ics` | [Queen's School of Computing calendar (Google Calendar iCal)](https://calendar.google.com/calendar/ical/nssp17qbbcimvjluc71msmvimc%40group.calendar.google.com/public/basic.ics) | **blocked** | not_checked | - | - | unknown | no | 2026-10-24 |
| `queens-ams-events` | [Queen's Alma Mater Society events (Tribe)](https://www.myams.org/wp-json/tribe/events/v1/events) | **allowed** | allowed | - | - | html_no_dates | yes | 2026-10-24 |
| `compsa-events` | [COMPSA (Queen's Computing Students' Association) events](https://compsa.ca/events) | **allowed** | allowed | - | - | html_no_dates | yes | 2026-10-24 |
| `stlawrence-eventscalendar` | [St. Lawrence College events calendar](https://www.stlawrencecollege.ca/eventscalendar) | **allowed** | allowed | [terms](https://www.stlawrencecollege.ca/terms-of-service) | terms: republishing | html | yes | 2026-10-24 |
| `trent-events` | [Trent University events](https://www.trentu.ca/events) | **allowed** | allowed | [terms](https://www.trentu.ca) | - | html | yes | 2026-10-24 |
| `trent-careerspace-expo` | [Trent Careerspace expos](https://www.trentu.ca/careerspace/expo) | **allowed** | allowed | [terms](https://www.trentu.ca) | - | html | yes | 2026-10-24 |
| `fleming-career-job-fairs` | [Fleming College Career Services job fairs and events](https://department.flemingcollege.ca/careers/career-job-fairs/) | **allowed** | allowed | - | - | html | yes | 2026-10-24 |
| `uottawa-cssa` | [uOttawa Computer Science Student Association (CSSA/AEI)](https://cssa-aei.ca/) | **allowed** | allowed | - | - | html_no_dates | yes | 2026-10-24 |
| `algonquin-sa-events` | [Algonquin Students' Association events (Tribe)](https://www.algonquinsa.com/wp-json/tribe/events/v1/events) | **allowed** | allowed | - | - | html | yes | 2026-10-24 |
| `algonquin-student-support-events` | [Algonquin Student Support Services / AC Hub events](https://www.algonquincollege.com/studentsupportservices/events/) | **allowed** | allowed | - | - | html | yes | 2026-10-24 |
| `algonquin-coop-career-fairs` | [Algonquin Co-op & Career Centre career fairs](https://www.algonquincollege.com/coop-career-centre/career-fairs/) | **allowed** | allowed | [terms](https://www.algonquincollege.com/coop-career-centre/terms-and-conditions/) | - | html_no_dates | yes | 2026-10-24 |
| `algonquin-events` | [Algonquin College main events page](https://www.algonquincollege.com/events/) | **allowed** | allowed | - | - | html | yes | 2026-10-24 |
| `laurentian-events` | [Laurentian University events](https://laurentian.ca/events) | **allowed** | allowed | [terms](https://laurentian.ca/academics/admissions/offers) | - | html | yes | 2026-10-24 |
| `lakehead-events` | [Lakehead University events](https://www.lakeheadu.ca/about/news-and-events/events) | **allowed** | allowed | [terms](https://www.lakeheadu.ca/about/news-and-events/events/events-archive/2026/node/351962) | - | html_no_dates | yes | 2026-10-24 |
| `nipissing-events` | [Nipissing University events](https://www.nipissingu.ca/events) | **blocked** | allowed | - | - | unknown | no | 2026-10-24 |
| `algoma-events` | [Algoma University events](https://algomau.ca/events/) | **allowed** | allowed | [terms](https://algomau.ca/privacy/notice-of-website-privacy/) | terms: republishing | html | yes | 2026-10-24 |
| `georgian-events` | [Georgian College events](https://www.georgiancollege.ca/events/) | **allowed** | no_robots | - | - | html_no_dates | yes | 2026-10-24 |
| `loyalist-events-tribe` | [Loyalist College events (Tribe)](https://loyalistcollege.com/wp-json/tribe/events/v1/events) | **allowed** | allowed | - | - | html | yes | 2026-10-24 |
| `cambrian-events` | [Cambrian College events](https://cambriancollege.ca/events/) | **allowed** | allowed | - | - | html | yes | 2026-10-24 |
| `northern-events` | [Northern College events & activities](https://www.northerncollege.ca/events/) | **allowed** | allowed | [terms](https://www.northerncollege.ca/terms/) | - | html_no_dates | yes | 2026-10-24 |
| `sault-career-fair` | [Sault College Annual Career Fair](https://www.saultcollege.ca/careerfair) | **allowed** | allowed | [terms](https://www.saultcollege.ca/legal) | - | html_no_dates | yes | 2026-10-24 |
| `invest-ottawa-events` | [Invest Ottawa event calendar](https://www.investottawa.ca/events/) | **allowed** | allowed | [terms](https://www.investottawa.ca/eventbrite-event/funding-your-future-a-legal-perspective/) | - | html | yes | 2026-10-24 |
| `techalliance-events` | [TechAlliance of Southwestern Ontario events](https://www.techalliance.ca/news/event-type/techalliance-events/) | **allowed** | allowed | [terms](https://www.techalliance.ca/terms-conditions/) | - | jsonld | yes | 2026-10-24 |
| `wetech-alliance-events` | [WEtech Alliance events (Windsor-Essex)](https://www.wetech-alliance.com/wp-json/tribe/events/v1/events) | **allowed** | allowed | - | - | tribe | yes | 2026-10-24 |
| `brock-experiencebu-rss` | [Brock University ExperienceBU events (Engage RSS)](https://experiencebu.brocku.ca/events.rss) | **allowed** | allowed | - | - | ics | yes | 2026-10-24 |
| `sheridan-ssu-engage-rss` | [Sheridan clubs (Engage RSS)](https://sheridancollege.campuslabs.ca/engage/events.rss) | **allowed** | allowed | - | - | ics | yes | 2026-10-24 |
| `western-events-json` | [Western University events (JSON)](https://www.uwo.ca/events/_data/current-live.json) | **allowed** | allowed | - | - | html | yes | 2026-10-24 |
| `carleton-events-api` | [Carleton University central events (WordPress REST)](https://events.carleton.ca/wp-json/wp/v2/cu_event?per_page=100) | **allowed** | allowed | - | - | html | yes | 2026-10-24 |
| `carleton-scs-events-api` | [Carleton School of Computer Science events (WordPress REST)](https://carleton.ca/scs/wp-json/wp/v2/cu_event?per_page=100) | **allowed** | allowed | [terms](https://carleton.ca/scs/wp-json/wp/v2/\"https:\/\/datascience.uchicago.edu\/people\/jie-jian\/\") | - | html | yes | 2026-10-24 |
| `carleton-career-events-api` | [Carleton Career Services events (WordPress REST)](https://carleton.ca/career/wp-json/wp/v2/cu_event?per_page=100) | **allowed** | allowed | [terms](https://carleton.ca/career/wp-json/wp/v2/\"https:\/\/www.exeter.ac.uk\/\") | - | html | yes | 2026-10-24 |
| `queens-events-rss` | [Queen's University events calendar (RSS)](https://www.queensu.ca/eventscalendar/calendar/rss/monthly/all) | **allowed** | allowed | - | - | html | yes | 2026-10-24 |
| `stclair-events-rss` | [St. Clair College events (RSS)](https://www.stclaircollege.ca/events.xml) | **allowed** | allowed | - | - | html | yes | 2026-10-24 |
| `hackathon:bearhacks` | [BearHacks](https://bearhacks.com/) | **allowed** | allowed | - | - | html_no_dates | yes | 2026-10-24 |
| `hackathon:calgaryhacks` | [CalgaryHacks](https://calgaryhacks.ca) | **allowed** | allowed | - | - | jsonld | yes | 2026-10-24 |
| `hackathon:centennialhacks` | [CentennialHacks](https://edu.ieee.org/ca-centennial-college/) | **allowed** | allowed | [terms](http://www.ieee.org/site_terms_conditions.html) | - | html_no_dates | yes | 2026-10-24 |
| `hackathon:computer-science-club-game-jam` | [Computer Science Club Game Jam](https://brockcsc.ca/events) | **allowed** | allowed | - | - | html_no_dates | yes | 2026-10-24 |
| `hackathon:conhacks` | [ConHacks](https://gdg.community.dev/events/details/google-gdg-on-campus-conestoga-college-waterloo-campus-waterloo-canada-presents-conhacks-2026-registrations-open/) | **blocked** | not_checked | - | - | unknown | no | 2026-10-24 |
| `hackathon:conuhacks` | [ConUHacks](https://conuhacks.io) | **allowed** | no_robots | - | - | html | yes | 2026-10-24 |
| `hackathon:cucai-canadian-undergraduate-conference-on-ai-run-by-qmind` | [CUCAI (Canadian Undergraduate Conference on AI, run by QMIND)](https://www.cs.queensu.ca/calendar) | **allowed** | allowed | - | - | ics | yes | 2026-10-24 |
| `hackathon:cuhacking` | [cuHacking](https://cuhacking.ca) | **allowed** | allowed | [terms](https://cuhacking.ca/terms) | - | html_no_dates | yes | 2026-10-24 |
| `hackathon:deerhacks` | [DeerHacks](https://deerhacks.ca/) | **allowed** | allowed | - | - | html_no_dates | yes | 2026-10-24 |
| `hackathon:deltahacks` | [DeltaHacks](https://deltahacks.com) | **allowed** | allowed | - | - | html | yes | 2026-10-24 |
| `hackathon:designathon-queen-s-ux-club` | [Designathon (Queen's UX Club)](https://www.cs.queensu.ca/calendar) | **allowed** | allowed | - | - | ics | yes | 2026-10-24 |
| `hackathon:ellehacks` | [ElleHacks](https://ellehacks.com) | **allowed** | no_robots | - | - | html_no_dates | yes | 2026-10-24 |
| `hackathon:eurekahacks` | [EurekaHacks](https://www.eurekahacks.ca/) | **allowed** | no_robots | - | - | html_no_dates | yes | 2026-10-24 |
| `hackathon:gdg-hacks` | [GDG Hacks](https://gdghacks.com/) | **allowed** | no_robots | - | - | html | yes | 2026-10-24 |
| `hackathon:gdg-hacks-guelph` | [GDG Hacks (Guelph)](https://gdg.community.dev/events/details/google-gdg-on-campus-university-of-guelph-guelph-canada-presents-gdg-hacks-3/) | **blocked** | not_checked | - | - | unknown | no | 2026-10-24 |
| `hackathon:genai-genesis` | [GenAI Genesis](https://genaigenesis.ca/) | **allowed** | allowed | - | - | html_no_dates | yes | 2026-10-24 |
| `hackathon:global-game-jam-site-game-development-program` | [Global Game Jam site (Game Development program)](https://educationnewscanada.com/article/education/region/ontario/27/745152/niagara-collegejanuary-28-2019-gamers-unite-at-niagara-college-for-fourth-annual-global-game-jam.html) | **allowed** | allowed | - | - | html | yes | 2026-10-24 |
| `hackathon:hack-canada` | [Hack Canada](https://hackcanada.org) | **allowed** | allowed | - | - | html | yes | 2026-10-24 |
| `hackathon:hack-club-events-canada` | [Hack Club events (Canada)](https://hackathons.hackclub.com/) | **allowed** | no_robots | [terms](https://www.losaltoshacks.com/) | - | html | yes | 2026-10-24 |
| `hackathon:hack-peel` | [Hack Peel](https://hackpeel.ca) | **allowed** | allowed | - | - | html_no_dates | yes | 2026-10-24 |
| `hackathon:hack-the-6ix` | [Hack the 6ix](https://hackthe6ix.com) | **allowed** | allowed | - | - | html | yes | 2026-10-24 |
| `hackathon:hack-the-hill` | [Hack the Hill](https://hackthehill.com) | **allowed** | allowed | [terms](https://cdn1.hackthehill.com/legal/privacy-policy.pdf) | - | jsonld | yes | 2026-10-24 |
| `hackathon:hack-the-north` | [Hack the North](https://hackthenorth.com) | **allowed** | allowed | - | - | html_no_dates | yes | 2026-10-24 |
| `hackathon:hack-the-valley` | [Hack the Valley](https://hackthevalley.io) | **allowed** | allowed | [terms](https://www.linkedin.com/in/danielle-andrea-santos-83974523a/) | - | html | yes | 2026-10-24 |
| `hackathon:hack-the-world-tmu` | [Hack the World (TMU)](https://www.torontomu.ca/innovation-boost-zone/hacktheworld/) | **allowed** | allowed | [terms](https://www.torontomu.ca/terms-conditions/) | terms: republishing | html | yes | 2026-10-24 |
| `hackathon:hack-western` | [Hack Western](https://hackwestern.com) | **allowed** | allowed | - | - | html | yes | 2026-10-24 |
| `hackathon:hackcanada-gdg-on-campus-laurier-co-hosted` | [HackCanada (GDG on Campus Laurier co-hosted)](https://gdg.community.dev/gdg-on-campus-wilfrid-laurier-university-waterloo-canada/) | **blocked** | not_checked | - | - | unknown | no | 2026-10-24 |
| `hackathon:hackhive` | [Hackhive](https://www.hackhive.ca/) | **unknown** | no_robots | - | - | unknown | no | 2026-10-24 |
| `hackathon:hacktrent` | [HackTrent](https://hacktrent.ca) | **allowed** | allowed | - | - | html_no_dates | yes | 2026-10-24 |
| `hackathon:hackville` | [Hackville](https://www.hackville.io) | **allowed** | allowed | - | - | jsonld | yes | 2026-10-24 |
| `hackathon:hawkhacks` | [HawkHacks](https://hawkhacks.ca) | **blocked** | disallowed | - | - | unknown | no | 2026-10-24 |
| `hackathon:humber-student-hackathon-cican-skills-for-success` | [Humber Student Hackathon (CICan Skills for Success)](https://humber.ca/staff/node/20354) | **blocked** | no_robots | - | - | unknown | no | 2026-10-24 |
| `hackathon:ignition-hacks` | [Ignition Hacks](https://www.ignitionhacks.org) | **allowed** | no_robots | - | - | html_no_dates | yes | 2026-10-24 |
| `hackathon:jamhacks` | [JAMHacks](https://jamhacks.ca) | **allowed** | allowed | - | - | html | yes | 2026-10-24 |
| `hackathon:makeuoft` | [MakeUofT](https://makeuoft.ca) | **allowed** | no_robots | [terms](https://github.com/MLH/mlh-policies/blob/main/contest-terms.md) | terms: republishing | html_no_dates | yes | 2026-10-24 |
| `hackathon:mathhacks` | [MathHacks](https://mathhacks.ca/) | **allowed** | allowed | - | - | jsonld | yes | 2026-10-24 |
| `hackathon:mchacks` | [McHacks](https://mchacks.ca) | **allowed** | no_robots | - | - | html | yes | 2026-10-24 |
| `hackathon:mcmaster-engineering-competition-mec` | [McMaster Engineering Competition (MEC)](https://macengsociety.ca/mec) | **blocked** | allowed | - | - | unknown | no | 2026-10-24 |
| `hackathon:mother-of-all-game-jams` | [Mother of All Game Jams](https://brockpress.com/students-can-learn-to-create-video-and-board-games-at-the-mother-of-all-game-jams/) | **allowed** | allowed | - | - | html | yes | 2026-10-24 |
| `hackathon:newhacks` | [NewHacks](https://newhacks.ca) | **blocked** | disallowed | - | - | unknown | no | 2026-10-24 |
| `hackathon:nwhacks` | [nwHacks](https://nwhacks.io) | **allowed** | allowed | - | - | html | yes | 2026-10-24 |
| `hackathon:onhacks` | [ONHacks](https://onhacks.ca) | **allowed** | no_robots | - | - | html_no_dates | yes | 2026-10-24 |
| `hackathon:qhacks` | [QHacks](https://qhacks.io) | **allowed** | no_robots | - | - | html_no_dates | yes | 2026-10-24 |
| `hackathon:redshifted-catalyst` | [Redshifted Catalyst](https://catalyst.redshifted.ca/) | **allowed** | allowed | - | - | html_no_dates | yes | 2026-10-24 |
| `hackathon:ru-hacks` | [RU Hacks](https://ruhacks.com) | **blocked** | disallowed | - | - | unknown | no | 2026-10-24 |
| `hackathon:school-of-advanced-technology-technology-project-showcase` | [School of Advanced Technology Technology Project Showcase](https://www.algonquincollege.com/news/2026/08/06/algonquin-college-technology-project-showcase-highlights-creative-solutions-and-technical-problem-solving/) | **allowed** | allowed | - | - | html | yes | 2026-10-24 |
| `hackathon:seneca-annual-hackathons-school-of-it-administration-securit` | [Seneca annual hackathons (School of IT Administration & Security)](https://students.senecapolytechnic.ca/spaces/14/school-of-information-technology-administration-security/wiki/view/7685/annual-hackathons) | **allowed** | allowed | [terms](https://students.senecapolytechnic.ca/spaces/14/school-of-information-technology-administration-security/albums) | - | html_no_dates | yes | 2026-10-24 |
| `hackathon:sheridan-adobe-design-hackathon` | [Sheridan / Adobe Design Hackathon](https://www.sheridancollege.ca/events/2026/02/hackathon) | **allowed** | allowed | [terms](https://www.sheridancollege.ca/privacy-legal) | terms: republishing | html | yes | 2026-10-24 |
| `hackathon:sheridan-datathon` | [Sheridan Datathon](https://gdg.community.dev/gdg-on-campus-sheridan-college-trafalgar-road-campus-oakville-canada/) | **blocked** | not_checked | - | - | unknown | no | 2026-10-24 |
| `hackathon:solutionhacks-gdg-on-campus-tmu` | [SolutionHacks (GDG on Campus TMU)](https://gdg.community.dev/gdg-on-campus-toronto-metropolitan-university-toronto-canada/) | **blocked** | not_checked | - | - | unknown | no | 2026-10-24 |
| `hackathon:spooky-game-jam-centre-for-digital-humanities` | [Spooky Game Jam (Centre for Digital Humanities)](https://brocku.ca/brock-news/in-focus/game-jam-a-spooktacular-success/) | **allowed** | allowed | - | - | html | yes | 2026-10-24 |
| `hackathon:spurhacks` | [SpurHacks](https://www.spurhacks.com) | **blocked** | disallowed | - | - | unknown | no | 2026-10-24 |
| `hackathon:technovation-waterloo-mini-hackathon-wics` | [Technovation Waterloo Mini-Hackathon (WiCS)](https://uwaterloo.ca/women-in-computer-science/events) | **allowed** | no_robots | [terms](https://uwaterloo.ca/copyright) | - | ics | yes | 2026-10-24 |
| `hackathon:terrahacks` | [TerraHacks](https://terrahacks.ca) | **allowed** | no_robots | - | - | html | yes | 2026-10-24 |
| `hackathon:unhack-yspace-lassonde` | [UNHACK (YSpace Lassonde)](https://events.yorku.ca/) | **allowed** | allowed | [terms](https://events.yorku.ca/events/socio-legal-studies-ma-phd/?occurrence=2026-10-13) | - | jsonld | yes | 2026-10-24 |
| `hackathon:uofthacks` | [UofTHacks](https://uofthacks.com) | **allowed** | no_robots | - | - | html_no_dates | yes | 2026-10-24 |
| `hackathon:uottahack` | [uOttaHack](https://uottahack.ca) | **allowed** | allowed | - | - | html_no_dates | yes | 2026-10-24 |
| `hackathon:utra-hacks` | [UTRA Hacks](https://hackathon.utra.ca/) | **allowed** | no_robots | - | - | html | yes | 2026-10-24 |
| `hackathon:uworcs-western-university-research-in-computer-science-confe` | [UWORCS (Western University Research in Computer Science conference)](https://www.uwo.ca/events/2026/04/western-university-research-in-computer-science-conference-uworcs.html) | **allowed** | allowed | - | - | ics | yes | 2026-10-24 |
| `hackathon:winhacks` | [WinHacks](https://www.winhacks.ca) | **allowed** | no_robots | - | - | html | yes | 2026-10-24 |

Terms quotes for each source are in `data/audit/<id>.json` (`terms_quotes`).
