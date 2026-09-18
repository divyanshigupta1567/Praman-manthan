import React from "react";
import Magnetic from "./Magnetic";

const LEAD_WORDS = ["Turn", "scattered", "civic", "complaints", "into"];
const TAIL_WORDS = ["a", "city", "can", "act", "on."];

export default function Hero({ onReport }) {
  return (
    <section className="hero" id="top">
      <div className="hero-copy" data-reveal>
        <span className="hero-eyebrow">
          <i className="hero-eyebrow-dot" aria-hidden="true" />
          प्रमाण · proof, evidence
        </span>
        <h1 className="hero-title">
          {LEAD_WORDS.map((w, i) => (
            <span className="reveal-word" style={{ "--i": i }} key={w}>
              {w}
            </span>
          ))}
          <em className="reveal-word" style={{ "--i": LEAD_WORDS.length }}>
            evidence
          </em>
          {TAIL_WORDS.map((w, i) => (
            <span className="reveal-word" style={{ "--i": LEAD_WORDS.length + 1 + i }} key={w}>
              {w}
            </span>
          ))}
        </h1>
        <p className="hero-lede">
          Praman collects complaints from citizens, clusters them by locality and category,
          and scores each cluster by how much pressure it is under. Instead of a queue of
          thousands of unrelated tickets, an operations team sees a short list of real
          incidents — ranked, mapped, and backed by the complaints that produced them.
        </p>
        <div className="hero-actions">
          <Magnetic as="button" type="button" className="btn-primary" onClick={onReport}>
            Report an issue
          </Magnetic>
          <a className="btn-secondary hero-btn-link" href="#board">
            View the live board
          </a>
        </div>
        <p className="hero-log">
          <span>Clustering: locality + category</span>
          <span>Refresh: every 15s</span>
          <span>Escalation: automatic</span>
        </p>
      </div>

      <aside className="hero-card" aria-label="How severity is banded" data-reveal data-reveal-delay="1" data-spotlight>
        <span className="hero-card-tab">Exhibit A</span>
        <span className="hero-card-label">Severity bands</span>
        <ul className="hero-band-list">
          <li>
            <i className="legend-dot" style={{ background: "#2E9E5B" }} />
            <span className="hero-band-name">Normal</span>
            <span className="hero-band-desc">Steady complaint volume, no intervention needed.</span>
          </li>
          <li>
            <i className="legend-dot" style={{ background: "#C4870F" }} />
            <span className="hero-band-name">Emerging</span>
            <span className="hero-band-desc">Volume climbing against the locality's own baseline.</span>
          </li>
          <li>
            <i className="legend-dot" style={{ background: "#D23B40" }} />
            <span className="hero-band-name">High Pressure</span>
            <span className="hero-band-desc">Spike and persistence both breached — auto-escalated.</span>
          </li>
        </ul>
        <p className="hero-card-note">
          Colour is reserved for severity alone. Nothing else on the board competes for it.
        </p>
        <img className="hero-card-watermark" src="/praman-logo.jpeg" alt="" aria-hidden="true" />
      </aside>
    </section>
  );
}
