import { useEffect } from "react";

// Observes every [data-reveal] element and adds .is-visible the first time
// it crosses into the viewport, then stops watching it. Marketing sections
// mount synchronously so their targets exist immediately; dashboard panels
// swap a skeleton for real content once their fetch resolves, so a
// MutationObserver keeps watching the DOM afterward and picks up any
// [data-reveal] node that appears later, without re-scanning everything.
export default function useScrollReveal() {
  useEffect(() => {
    if (!("IntersectionObserver" in window)) {
      document.querySelectorAll("[data-reveal]").forEach((el) => el.classList.add("is-visible"));
      return undefined;
    }

    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            entry.target.classList.add("is-visible");
            observer.unobserve(entry.target);
          }
        });
      },
      { threshold: 0.12, rootMargin: "0px 0px -8% 0px" }
    );

    const seen = new WeakSet();
    const observeNew = (root) => {
      const nodes = root.matches?.("[data-reveal]") ? [root] : [];
      nodes.push(...root.querySelectorAll?.("[data-reveal]") ?? []);
      nodes.forEach((el) => {
        if (seen.has(el)) return;
        seen.add(el);
        observer.observe(el);
      });
    };

    observeNew(document.body);

    const mutationObserver = new MutationObserver((mutations) => {
      mutations.forEach((mutation) => {
        mutation.addedNodes.forEach((node) => {
          if (node.nodeType === 1) observeNew(node);
        });
      });
    });
    mutationObserver.observe(document.body, { childList: true, subtree: true });

    return () => {
      observer.disconnect();
      mutationObserver.disconnect();
    };
  }, []);
}
