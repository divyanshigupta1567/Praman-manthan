import React, { useCallback, useEffect, useMemo, useRef, useState } from "react";
import KPIRow from "./components/KPIRow";
import AutoEscalationBanner from "./components/AutoEscalationBanner";
import MapView from "./components/MapView";
import IncidentList from "./components/IncidentList";
import ComparisonView from "./components/ComparisonView";
import FilterBar from "./components/FilterBar";
import ToastContainer from "./components/ToastContainer";
import EvidencePanel from "./components/EvidencePanel";
import TrendChart from "./components/TrendChart";
import BriefingPanel from "./components/BriefingPanel";
import ComplaintForm from "./components/ComplaintForm";
import { getComplaints, getIncidents, getHotspots, getMetrics, getTrends, getBriefing, ApiError } from "./api";

// One slice of state per section: { data, loading, error }. Each section
// fetches, loads, and fails independently — a slow or broken endpoint
// never blocks or blanks the rest of the dashboard.
function useSection(fetchFn) {
  const [state, setState] = useState({ data: null, loading: true, error: null });

  const load = useCallback(() => {
    setState((s) => ({ ...s, loading: true, error: null }));
    fetchFn()
      .then((data) => setState({ data, loading: false, error: null }))
      .catch((err) =>
        setState({
          data: null,
          loading: false,
          error: err instanceof ApiError ? err.message : "Something went wrong.",
        })
      );
  }, [fetchFn]);

  useEffect(() => {
    load();
  }, [load]);

  return [state, load];
}

export default function Dashboard() {
  const [complaintsState, reloadComplaints] = useSection(getComplaints);
  const [incidentsState, reloadIncidents] = useSection(getIncidents);
  const [hotspotsState, reloadHotspots] = useSection(getHotspots);
  const [metricsState, reloadMetrics] = useSection(getMetrics);
  const [trendsState, reloadTrends] = useSection(getTrends);
  const [briefingState, reloadBriefing] = useSection(getBriefing);

  const [selectedIncidentId, setSelectedIncidentId] = useState(null);
  const [formOpen, setFormOpen] = useState(false);

  // Toast notification state (defined first so subsequent callbacks can use addToast)
  const [toasts, setToasts] = useState([]);
  const addToast = useCallback((toast) => {
    const id = `toast-${Date.now()}-${Math.random().toString(36).substring(2, 6)}`;
    setToasts((prev) => [...prev, { ...toast, id }]);
  }, []);
  const removeToast = useCallback((id) => {
    setToasts((prev) => prev.filter((t) => t.id !== id));
  }, []);

  // Incident comparison state (2-3 incidents side-by-side)
  const [comparingIds, setComparingIds] = useState([]);
  const [comparisonOpen, setComparisonOpen] = useState(false);

  const handleToggleCompare = useCallback((id) => {
    setComparingIds((prev) => {
      if (prev.includes(id)) {
        const next = prev.filter((item) => item !== id);
        if (next.length < 2) setComparisonOpen(false);
        return next;
      }
      if (prev.length >= 3) {
        addToast({
          type: "info",
          title: "Comparison Limit",
          message: "You can compare up to 3 incidents at a time.",
        });
        return prev;
      }
      const next = [...prev, id];
      if (next.length >= 2) {
        setComparisonOpen(true);
      }
      return next;
    });
  }, [addToast]);

  const handleRemoveFromCompare = useCallback((id) => {
    setComparingIds((prev) => {
      const next = prev.filter((item) => item !== id);
      if (next.length < 2) setComparisonOpen(false);
      return next;
    });
  }, []);

  // Track auto-escalated incidents to notify on arrival
  const knownEscalatedIdsRef = useRef(new Set());
  useEffect(() => {
    if (!incidentsState.data) return;

    const escalated = incidentsState.data.filter((i) => i.auto_escalated);
    const newArrivals = escalated.filter(
      (i) => !knownEscalatedIdsRef.current.has(i.incident_id)
    );

    if (newArrivals.length > 0) {
      newArrivals.forEach((i) => {
        knownEscalatedIdsRef.current.add(i.incident_id);
        addToast({
          type: "escalation",
          title: "Auto-Escalation Alert",
          message: `${i.incident_id} (${i.locality} · ${i.category}) flagged as High Pressure.`,
        });
      });
    }
  }, [incidentsState.data, addToast]);

  // Client-side filter states
  const [severityFilter, setSeverityFilter] = useState("all");
  const [categoryFilter, setCategoryFilter] = useState("all");
  const [searchQuery, setSearchQuery] = useState("");

  const allIncidents = incidentsState.data || [];

  // Extract unique categories dynamically from incidents
  const categories = useMemo(() => {
    const cats = new Set(allIncidents.map((i) => i.category).filter(Boolean));
    return Array.from(cats).sort();
  }, [allIncidents]);

  // Pure client-side filtered incidents
  const filteredIncidents = useMemo(() => {
    return allIncidents.filter((incident) => {
      if (severityFilter !== "all" && incident.severity_band !== severityFilter) {
        return false;
      }
      if (categoryFilter !== "all" && incident.category !== categoryFilter) {
        return false;
      }
      if (searchQuery.trim()) {
        const query = searchQuery.trim().toLowerCase();
        const locality = (incident.locality || "").toLowerCase();
        if (!locality.includes(query)) {
          return false;
        }
      }
      return true;
    });
  }, [allIncidents, severityFilter, categoryFilter, searchQuery]);

  const hasActiveFilters =
    severityFilter !== "all" || categoryFilter !== "all" || searchQuery.trim() !== "";

  // Derive filtered hotspots in lockstep with filtered incidents
  const filteredHotspots = useMemo(() => {
    const allHotspots = hotspotsState.data || [];
    if (!hasActiveFilters) return allHotspots;
    const allowedIds = new Set(filteredIncidents.map((i) => i.incident_id));
    return allHotspots.filter((h) => allowedIds.has(h.incident_id));
  }, [hotspotsState.data, filteredIncidents, hasActiveFilters]);

  const handleResetFilters = useCallback(() => {
    setSeverityFilter("all");
    setCategoryFilter("all");
    setSearchQuery("");
  }, []);

  const onSelectIncident = useCallback((incidentId) => {
    setSelectedIncidentId(incidentId);
  }, []);

  const closeEvidencePanel = useCallback(() => setSelectedIncidentId(null), []);

  // Map for the Evidence Panel's sample-complaint fallback lookup.
  const complaintsById = new Map((complaintsState.data || []).map((c) => [c.complaint_id, c]));

  return (
    <div className="dashboard-root">
      <AutoEscalationBanner incidents={incidentsState.data} onSelectIncident={onSelectIncident} />

      <header className="dashboard-header">
        <h1>Spandan</h1>
        <p className="dashboard-subtitle">Civic complaint intelligence — live operations view</p>
        <button type="button" className="btn-primary btn-report" onClick={() => setFormOpen(true)}>
          Report an issue
        </button>
      </header>

      <KPIRow
        metrics={metricsState.data}
        loading={metricsState.loading}
        error={metricsState.error}
        onRetry={reloadMetrics}
      />

      {/* Client-side filter bar above IncidentList/map */}
      <FilterBar
        severity={severityFilter}
        onSeverityChange={setSeverityFilter}
        category={categoryFilter}
        onCategoryChange={setCategoryFilter}
        categories={categories}
        searchQuery={searchQuery}
        onSearchChange={setSearchQuery}
        totalCount={allIncidents.length}
        filteredCount={filteredIncidents.length}
        onReset={handleResetFilters}
      />

      <div className="dashboard-main">
        <MapView
          hotspots={filteredHotspots}
          loading={hotspotsState.loading}
          error={hotspotsState.error}
          onRetry={reloadHotspots}
          onSelectIncident={onSelectIncident}
          selectedIncidentId={selectedIncidentId}
        />
        <IncidentList
          incidents={filteredIncidents}
          loading={incidentsState.loading}
          error={incidentsState.error}
          onRetry={reloadIncidents}
          onSelectIncident={onSelectIncident}
          selectedIncidentId={selectedIncidentId}
          isFiltered={hasActiveFilters}
          comparingIds={comparingIds}
          onToggleCompare={handleToggleCompare}
          onOpenComparison={() => setComparisonOpen(true)}
        />
      </div>

      <div className="dashboard-bottom">
        <TrendChart
          trends={trendsState.data}
          loading={trendsState.loading}
          error={trendsState.error}
          onRetry={reloadTrends}
        />
        <BriefingPanel
          briefing={briefingState.data}
          loading={briefingState.loading}
          error={briefingState.error}
          onRetry={reloadBriefing}
          onSelectIncident={onSelectIncident}
        />
      </div>

      {/* ComparisonView split panel for 2-3 incidents */}
      <ComparisonView
        incidentIds={comparingIds}
        isOpen={comparisonOpen && comparingIds.length >= 2}
        onClose={() => setComparisonOpen(false)}
        onRemoveIncident={handleRemoveFromCompare}
      />

      {/* EvidencePanel is always mounted — open/close is CSS-driven so
          the slide-out transition plays before content disappears. */}
      <EvidencePanel
        incidentId={selectedIncidentId}
        complaintsById={complaintsById}
        onClose={closeEvidencePanel}
        isOpen={!!selectedIncidentId}
      />

      {formOpen && (
        <ComplaintForm
          onClose={() => setFormOpen(false)}
          onSubmitted={() => {
            reloadComplaints();
            reloadIncidents();
            reloadHotspots();
            reloadMetrics();
          }}
          onToast={addToast}
        />
      )}

      {/* Lightweight toast notification container with 4s auto-dismiss */}
      <ToastContainer toasts={toasts} onDismiss={removeToast} />
    </div>
  );
}
