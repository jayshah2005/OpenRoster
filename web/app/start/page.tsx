import type { Metadata } from "next";
import Link from "next/link";

export const metadata: Metadata = {
  title: "Start here",
  description: "How to use OpenRoster, what each kind of opportunity is, and how to get ready for it.",
};

// The early-career guide. Copy follows .claude/skills/humanizer: plain sentences, no invented facts.
export default function StartPage() {
  return (
    <article className="prose">
      <h1>Start here</h1>
      <p className="lede">
        OpenRoster lists events and programs that help computer science students meet employers, build things and find
        their first roles. Everything is free to browse, and every listing links to the organizer&apos;s own page.
      </p>

      <nav aria-label="On this page" className="toc">
        <a href="#use">Using the site</a> · <a href="#types">What each type is</a> ·{" "}
        <a href="#prep">Getting ready</a> · <a href="#timing">When things happen</a> ·{" "}
        <a href="#roles">Volunteering, mentoring and judging</a>
      </nav>

      <h2 id="use">Using the site</h2>
      <p>
        The <Link href="/">list</Link> puts the nearest application deadline first, because that is what you are most
        likely to miss. Pick what you want to do (attend, volunteer, mentor, judge) and a type, or open More filters to
        narrow by school, distance, date, eligibility or who an event is for. Tick &quot;Only show what is open for
        applications now&quot; when you want something you can apply to today.
      </p>
      <p>
        Filters live in the page address, so you can bookmark a view or send it to a friend. Every view has a calendar
        link. Subscribe to it in Google Calendar, Apple Calendar or Outlook and new events appear on their own, along
        with an &quot;Apply by&quot; reminder the day before each deadline. There is also an RSS feed for each view and
        a <Link href="/digest/">weekly digest</Link>.
      </p>
      <p>
        Each listing shows when we last checked it. Dates sometimes change, so confirm on the organizer&apos;s page
        before you plan around one.
      </p>

      <h2 id="types">What each type is</h2>
      <dl className="glossary">
        <dt>Hackathon</dt>
        <dd>
          A weekend (sometimes a day) where you build a project in a small team. Most student hackathons are free, have
          food, and welcome people who have never been to one. Some cover travel.
        </dd>
        <dt>Info session</dt>
        <dd>
          A company presents its teams and student roles, then takes questions. Recruiters often attend, so it is a good
          place to ask how their hiring works and to get a name to follow up with.
        </dd>
        <dt>Tech talk</dt>
        <dd>A talk, panel or seminar on a technical or career topic. Low pressure and good for learning what a field is like.</dd>
        <dt>Career fair</dt>
        <dd>Many employers at tables in one place. Bring a short introduction and a resume, and research a few companies first.</dd>
        <dt>Networking</dt>
        <dd>Mixers and meetups where students, alumni and people working in tech talk informally.</dd>
        <dt>Workshop</dt>
        <dd>A hands-on session: resume reviews, interview practice, or learning a tool or language.</dd>
        <dt>Conference</dt>
        <dd>A day or more of talks and workshops. Student conferences such as CUTC and CUSEC often look for volunteers.</dd>
        <dt>Case competition</dt>
        <dd>Teams solve a business or technical problem and present to judges. Some are aimed at first- and second-year students.</dd>
        <dt>Early-career program</dt>
        <dd>
          Insight days, fellowships, externships and programs for first- and second-year students. They often lead to
          internship interviews later. See the <Link href="/programs/">programs directory</Link>.
        </dd>
      </dl>

      <h2 id="prep">Getting ready</h2>
      <h3>Before an info session or career fair</h3>
      <ul>
        <li>Read the company&apos;s student careers page and pick one team you are curious about.</li>
        <li>Prepare one or two questions you could not answer from their website, such as how interns are matched to teams.</li>
        <li>Have a one-page resume ready as a PDF. Your school&apos;s career centre will review it for free.</li>
        <li>Afterwards, send a short thank-you note to anyone you spoke with, and mention something from the conversation.</li>
      </ul>
      <h3>Your first hackathon</h3>
      <ul>
        <li>You do not need a team or an idea beforehand. Most hackathons run team-forming at the start.</li>
        <li>Apply early. Popular events fill up, and some accept people in waves.</li>
        <li>Aim for a small project that works. A clear demo of one feature beats an unfinished big idea.</li>
        <li>Put the project on GitHub with a short README. It gives you something concrete to talk about in interviews.</li>
      </ul>
      <h3>Applying to programs</h3>
      <ul>
        <li>Many programs ask short-answer questions. Draft them in a document first and keep them for the next application.</li>
        <li>Check eligibility carefully: year of study, program, and sometimes citizenship or school.</li>
        <li>Use the calendar feed so deadlines do not slip past you.</li>
      </ul>

      <h2 id="timing">When things happen</h2>
      <p>
        Timing varies by company and school, but some patterns repeat each year in Canada. Large tech companies and banks
        often open the next summer&apos;s internships in late summer and fall, and run most campus info sessions from
        September to November. Programs for first- and second-year students frequently open in the fall and winter.
        Student hackathons run all year, with many between September and March. Co-op students should also follow their
        school&apos;s own job board, which OpenRoster cannot see because it needs a login.
      </p>

      <h2 id="roles">Volunteering, mentoring and judging</h2>
      <p>
        Hackathons and conferences need volunteers to run check-in, food and logistics, and they usually say so on their
        own sites weeks before the event. Volunteering is free, you meet the organizers and sponsors, and some events let
        volunteers attend talks. Once you have built a few projects, mentoring means helping teams debug during the event.
        Judging is usually for people with more experience. Choose &quot;volunteer&quot;, &quot;mentor&quot; or
        &quot;judge&quot; under &quot;I want to&quot; to see open calls.
      </p>

      <h2>Missing something?</h2>
      <p>
        If you know about an event, a club calendar or a program we do not list, <Link href="/contribute/">add it</Link>.
        It takes a couple of minutes and helps the next person find it.
      </p>
    </article>
  );
}
