import React from "react";

const FEATURES = [
  {
    title: "Complaints become incidents",
    body: "Raw reports are grouped by locality and category, so ninety complaints about one broken drain read as one incident with ninety pieces of evidence behind it — not ninety rows to work through.",
  },
  {
    title: "Pressure scoring, not vote counting",
    body: "Each incident is scored on spike and persistence against its own locality's baseline. A quiet ward with an unusual week outranks a busy ward having a normal one.",
  },
  {
    title: "Automatic escalation",
    body: "When an incident breaches both thresholds it is banded High Pressure, pinned to the top of the board, and announced — no one has to be watching for it to be caught.",
  },
  {
    title: "Every number is traceable",
    body: "Open any incident and the evidence panel shows the underlying complaints, their IDs and their current status. Nothing on the board is a figure you cannot follow back to its source.",
  },
  {
    title: "Side-by-side comparison",
    body: "Put two or three incidents next to each other to settle what gets the crew today: scores, spike, complaint volume and seven-day trend, aligned on the same rows.",
  },
  {
    title: "Live, and pausable",
    body: "The board refreshes every fifteen seconds without blanking the screen. Presenting to a room? Pause it and the view holds still while you talk.",
  },
];

const STEPS = [
  {
    n: "01",
    title: "A citizen reports",
    body: "A complaint is filed with a location, a category and a description. It takes under a minute and needs no account.",
  },
  {
    n: "02",
    title: "Praman clusters it",
    body: "The complaint joins an existing incident for that locality and category, or opens a new one if nothing matches.",
  },
  {
    n: "03",
    title: "The cluster gets scored",
    body: "Spike and persistence are recomputed against the locality's baseline, producing a severity band and a rank.",
  },
  {
    n: "04",
    title: "Operations acts",
    body: "The board surfaces what moved, the briefing summarises why, and the evidence panel shows exactly who reported it.",
  },
];

export function WhatSection() {
  return (
    <section className="site-section" id="what">
      <div className="section-head" data-reveal>
        <span className="section-eyebrow">What it does</span>
        <h2>A shorter list, with the reasoning attached</h2>
        <p>
          Praman sits between the people reporting problems and the team fixing them. Its job
          is to decide what deserves attention next and to show its working.
        </p>
      </div>
      <div className="feature-bento">
        {FEATURES.map((f, i) => (
          <article
            className="feature-card"
            key={f.title}
            data-reveal
            data-reveal-delay={i % 3}
            data-spotlight
          >
            <span className="feature-num">{String(i + 1).padStart(2, "0")}</span>
            <h3>{f.title}</h3>
            <p>{f.body}</p>
          </article>
        ))}
      </div>
    </section>
  );
}

export function HowSection() {
  return (
    <section className="site-section" id="how">
      <div className="section-head" data-reveal>
        <span className="section-eyebrow">How it works</span>
        <h2>From one report to a ranked incident</h2>
      </div>
      <ol className="step-row">
        {STEPS.map((s, i) => (
          <li className="step-card" key={s.n} data-reveal data-reveal-delay={i % 4} data-spotlight>
            <span className="step-num">{s.n}</span>
            <h3>{s.title}</h3>
            <p>{s.body}</p>
          </li>
        ))}
      </ol>
    </section>
  );
}
