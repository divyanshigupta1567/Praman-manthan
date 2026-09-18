import React, { useEffect, useState } from "react";
import Magnetic from "./Magnetic";

const LINKS = [
  { href: "#what", label: "What it does" },
  { href: "#how", label: "How it works" },
  { href: "#board", label: "Live board" },
];

export default function SiteNav({ onReport }) {
  const [scrolled, setScrolled] = useState(false);

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 12);
    onScroll();
    window.addEventListener("scroll", onScroll, { passive: true });
    return () => window.removeEventListener("scroll", onScroll);
  }, []);

  return (
    <header className={`site-nav ${scrolled ? "site-nav--scrolled" : ""}`}>
      <div className="site-nav-inner">
        <a className="brand" href="#top">
          <img className="brand-mark" src="/praman-logo.jpeg" alt="Praman" />
          <span className="brand-text">
            <strong>Praman</strong>
            <span className="brand-tag">Civic Evidence Platform</span>
          </span>
        </a>

        <nav className="site-nav-links" aria-label="Primary">
          {LINKS.map((l) => (
            <a key={l.href} href={l.href}>
              {l.label}
            </a>
          ))}
        </nav>

        <Magnetic as="button" type="button" className="btn-primary btn-sm" onClick={onReport} strength={10}>
          Report an issue
        </Magnetic>
      </div>
    </header>
  );
}
