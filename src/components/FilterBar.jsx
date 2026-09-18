import React, { useEffect, useState } from "react";
import { SEVERITY_COLOR } from "../severityColors";

const SEVERITIES = [
  { value: "all", label: "All Severities" },
  { value: "High Pressure", label: "High Pressure", color: SEVERITY_COLOR["High Pressure"] },
  { value: "Emerging", label: "Emerging", color: SEVERITY_COLOR.Emerging },
  { value: "Normal", label: "Normal", color: SEVERITY_COLOR.Normal },
];

export default function FilterBar({
  severity = "all",
  onSeverityChange,
  category = "all",
  onCategoryChange,
  categories = [],
  searchQuery = "",
  onSearchChange,
  filteredCount = 0,
  totalCount = 0,
  onReset,
}) {
  const [localSearch, setLocalSearch] = useState(searchQuery);

  // Debounce search input by 300ms
  useEffect(() => {
    const timer = setTimeout(() => {
      onSearchChange(localSearch);
    }, 300);
    return () => clearTimeout(timer);
  }, [localSearch, onSearchChange]);

  // Keep local search in sync if reset from outside
  useEffect(() => {
    setLocalSearch(searchQuery);
  }, [searchQuery]);

  const hasActiveFilters = severity !== "all" || category !== "all" || searchQuery.trim() !== "";

  return (
    <div className="filter-bar" aria-label="Incident filters" data-reveal>
      <div className="filter-group-left">
        {/* Severity Band Pills */}
        <div className="filter-pills" role="radiogroup" aria-label="Filter by severity">
          {SEVERITIES.map((s) => {
            const isActive = severity === s.value;
            return (
              <button
                key={s.value}
                type="button"
                className={`filter-pill ${isActive ? "filter-pill--active" : ""}`}
                onClick={() => onSeverityChange(s.value)}
                role="radio"
                aria-checked={isActive}
              >
                {s.color && (
                  <span
                    className="filter-pill-dot"
                    style={{ background: s.color }}
                    aria-hidden="true"
                  />
                )}
                <span>{s.label}</span>
              </button>
            );
          })}
        </div>

        {/* Category Dropdown */}
        <div className="filter-category-wrap">
          <label htmlFor="category-filter" className="sr-only">
            Filter by category
          </label>
          <select
            id="category-filter"
            className="filter-select"
            value={category}
            onChange={(e) => onCategoryChange(e.target.value)}
          >
            <option value="all">All Categories</option>
            {categories.map((cat) => (
              <option key={cat} value={cat}>
                {cat}
              </option>
            ))}
          </select>
        </div>
      </div>

      <div className="filter-group-right">
        {/* Debounced Search by Locality */}
        <div className="filter-search-wrap">
          <svg
            className="filter-search-icon"
            viewBox="0 0 20 20"
            fill="none"
            stroke="currentColor"
            aria-hidden="true"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth="2"
              d="M19 19l-4.35-4.35M17 9A8 8 0 1 1 1 9a8 8 0 0 1 16 0z"
            />
          </svg>
          <input
            type="text"
            className="filter-search-input"
            placeholder="Search area or locality…"
            value={localSearch}
            onChange={(e) => setLocalSearch(e.target.value)}
            aria-label="Filter incidents by area or locality name"
          />
          {localSearch && (
            <button
              type="button"
              className="filter-search-clear"
              onClick={() => {
                setLocalSearch("");
                onSearchChange("");
              }}
              aria-label="Clear locality search"
            >
              ×
            </button>
          )}
        </div>

        {/* Status Count & Reset Button */}
        {hasActiveFilters && (
          <div className="filter-status">
            <span className="filter-count">
              Showing {filteredCount} of {totalCount}
            </span>
            <button
              type="button"
              className="btn-filter-reset"
              onClick={onReset}
              aria-label="Reset all filters"
            >
              Reset
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
