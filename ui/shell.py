"""Enterprise Streamlit shell components for Bri.

These components make Bri feel like a complete product surface instead of a
single-purpose prototype. They intentionally consume typed middle-layer objects
from ``services.application`` rather than raw database rows or HTTP payloads.
"""

from __future__ import annotations

import html
from collections.abc import Iterable

import streamlit as st

from services.application import DashboardSnapshot, PersistenceReadiness, VideoSummary
from services.mcp_client import VideoProgress

STATUS_COLORS = {
    "complete": "#40E0D0",
    "completed": "#40E0D0",
    "processing": "#BA68C8",
    "pending": "#FFB86C",
    "error": "#FF6B6B",
    "unknown": "#A0A0A0",
}


def render_product_header(snapshot: DashboardSnapshot | None = None) -> None:
    """Render the top-level product header and enterprise readiness strip."""

    mcp_label = "Online" if snapshot and snapshot.mcp_health.online else "Local mode"
    mcp_color = "#40E0D0" if snapshot and snapshot.mcp_health.online else "#FFB86C"
    video_count = snapshot.total_videos if snapshot else 0
    ready_count = snapshot.ready_videos if snapshot else 0

    st.markdown(
        f"""
        <section class="bri-hero" role="banner" aria-label="Bri product overview">
            <div class="bri-hero-copy">
                <p class="bri-eyebrow">Empathetic Video Intelligence</p>
                <h1>BRI turns video into conversation, context, and memory.</h1>
                <p class="bri-hero-subtitle">
                    Upload a video, let the FastAPI MCP service enrich it with multimodal tools,
                    and ask natural questions through a polished Streamlit product interface.
                </p>
            </div>
            <div class="bri-readiness-card">
                <div><span>Service</span><strong style="color:{mcp_color}">{mcp_label}</strong></div>
                <div><span>Library</span><strong>{video_count} videos</strong></div>
                <div><span>Ready</span><strong>{ready_count} analyzed</strong></div>
            </div>
        </section>
        """,
        unsafe_allow_html=True,
    )


def render_dashboard(snapshot: DashboardSnapshot) -> None:
    """Render product, service, and workflow metrics."""

    st.markdown("### Production command center")
    metric_cols = st.columns(5)
    metric_cols[0].metric("Videos", snapshot.total_videos)
    metric_cols[1].metric("Ready", snapshot.ready_videos)
    metric_cols[2].metric("Processing", snapshot.processing_videos)
    metric_cols[3].metric("Queued", snapshot.pending_videos)
    metric_cols[4].metric("Messages", snapshot.conversations)

    status = "Online" if snapshot.mcp_health.online else "Offline"
    status_color = "#40E0D0" if snapshot.mcp_health.online else "#FFB86C"
    tools = (
        ", ".join(tool.name for tool in snapshot.tools[:6])
        or "Tool catalog unavailable in local mode"
    )
    st.markdown(
        f"""
        <div class="bri-system-panel" role="status" aria-live="polite">
            <div>
                <span class="bri-panel-label">FastAPI MCP service</span>
                <strong style="color:{status_color}">{status}</strong>
                <small>{html.escape(snapshot.mcp_health.url)}</small>
            </div>
            <div>
                <span class="bri-panel-label">Multimodal tools</span>
                <strong>{len(snapshot.tools)} discovered</strong>
                <small>{html.escape(tools)}</small>
            </div>
            <div>
                <span class="bri-panel-label">Data layer</span>
                <strong>SQLite durable</strong>
                <small>Videos, processing state, memory, and artifacts</small>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_video_workflow(videos: Iterable[VideoSummary]) -> None:
    """Render a compact workflow board for recently uploaded videos."""

    videos = list(videos)[:6]
    if not videos:
        st.info("Upload your first video to activate Bri's analysis workflow.")
        return

    st.markdown("### Active video workflow")
    cols = st.columns(min(3, max(1, len(videos))))
    for index, video in enumerate(videos):
        color = STATUS_COLORS.get(video.processing_status, STATUS_COLORS["unknown"])
        with cols[index % len(cols)]:
            st.markdown(
                f"""
                <article class="bri-video-card">
                    <div class="bri-video-status" style="border-color:{color}; color:{color}">{html.escape(video.status_label)}</div>
                    <h4>{html.escape(video.filename)}</h4>
                    <p>{html.escape(video.duration_label)} · {html.escape(video.video_id[:8])}</p>
                </article>
                """,
                unsafe_allow_html=True,
            )


def render_persistence_panel(readiness: PersistenceReadiness | None) -> None:
    """Render SQLite durability, backup posture, and integrity status."""

    st.markdown("### Persistence readiness")
    if readiness is None:
        st.info("Persistence readiness is unavailable until the database is initialized.")
        return

    integrity = readiness.integrity
    status = "Healthy" if readiness.ok else "Needs attention"
    status_color = "#40E0D0" if readiness.ok else "#FFB86C"
    journal_mode = readiness.production_settings.get("journal_mode", integrity.journal_mode)
    st.markdown(
        f"""
        <div class="bri-system-panel" role="status" aria-live="polite">
            <div>
                <span class="bri-panel-label">SQLite integrity</span>
                <strong style="color:{status_color}">{html.escape(status)}</strong>
                <small>{html.escape("; ".join(integrity.messages))}</small>
            </div>
            <div>
                <span class="bri-panel-label">Durability mode</span>
                <strong>{html.escape(str(journal_mode).upper())}</strong>
                <small>{integrity.page_count} pages · {integrity.freelist_count} free pages</small>
            </div>
            <div>
                <span class="bri-panel-label">WAL checkpoint</span>
                <strong>{integrity.wal_checkpoint.get("checkpointed_frames", 0)} frames</strong>
                <small>{html.escape(integrity.database_path)}</small>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_progress_panel(progress: VideoProgress | None) -> None:
    """Render staged multimodal processing progress for a selected video."""

    if progress is None:
        st.info("Processing telemetry is unavailable while the MCP service is offline.")
        return

    percent = max(0.0, min(100.0, float(progress.progress_percent)))
    st.markdown("### Processing intelligence pipeline")
    st.progress(percent / 100.0, text=f"{progress.stage.title()} · {percent:.0f}%")
    st.caption(html.escape(progress.message))
    cols = st.columns(4)
    cols[0].metric("Frames", progress.frames_extracted)
    cols[1].metric("Captions", progress.captions_generated)
    cols[2].metric("Transcript", progress.transcript_segments)
    cols[3].metric("Objects", progress.objects_detected)


def render_sidebar_readiness(snapshot: DashboardSnapshot) -> None:
    """Render concise full-stack readiness inside the sidebar."""

    service_icon = "●"
    service_color = "#40E0D0" if snapshot.mcp_health.online else "#FFB86C"
    st.markdown("#### Stack readiness")
    st.markdown(
        f"""
        <div class="bri-sidebar-readiness">
            <div><span style="color:{service_color}">{service_icon}</span> MCP service</div>
            <div>● Streamlit product UI</div>
            <div>● SQLite persistence</div>
            <div>● Middle-layer facade</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_enterprise_styles() -> None:
    """Inject enterprise shell CSS on top of Bri's existing theme."""

    st.markdown(
        """
        <style>
        .bri-hero {
            display: grid;
            grid-template-columns: minmax(0, 1.7fr) minmax(260px, 0.8fr);
            gap: 1.25rem;
            align-items: stretch;
            padding: 1.35rem;
            margin: 0.25rem 0 1.25rem 0;
            border: 1px solid #333333;
            border-radius: 22px;
            background: radial-gradient(circle at top left, rgba(186, 104, 200, 0.24), transparent 32%),
                        linear-gradient(135deg, #151018 0%, #101010 100%);
            box-shadow: 0 18px 60px rgba(0,0,0,0.28);
        }
        .bri-eyebrow {
            text-transform: uppercase;
            letter-spacing: 0.14em;
            color: #40E0D0 !important;
            font-size: 0.78rem;
            font-weight: 700;
            margin-bottom: 0.4rem;
        }
        .bri-hero h1 {
            margin: 0 0 0.75rem 0;
            font-size: clamp(2rem, 4vw, 3.2rem);
            line-height: 1.02;
        }
        .bri-hero-subtitle {
            max-width: 780px;
            color: #d7d7d7 !important;
            font-size: 1.02rem;
            line-height: 1.65;
        }
        .bri-readiness-card, .bri-system-panel, .bri-video-card {
            border: 1px solid #333333;
            border-radius: 18px;
            background: rgba(42, 42, 42, 0.72);
            backdrop-filter: blur(14px);
        }
        .bri-readiness-card {
            padding: 1rem;
            display: grid;
            gap: 0.8rem;
        }
        .bri-readiness-card div, .bri-system-panel div {
            display: grid;
            gap: 0.15rem;
        }
        .bri-readiness-card span, .bri-panel-label {
            color: #a0a0a0 !important;
            font-size: 0.78rem;
            text-transform: uppercase;
            letter-spacing: 0.08em;
        }
        .bri-readiness-card strong, .bri-system-panel strong {
            font-size: 1.1rem;
        }
        .bri-system-panel {
            display: grid;
            grid-template-columns: repeat(3, minmax(0, 1fr));
            gap: 1rem;
            padding: 1rem;
            margin: 0.75rem 0 1.25rem;
        }
        .bri-system-panel small {
            color: #a0a0a0 !important;
            overflow-wrap: anywhere;
        }
        .bri-video-card {
            padding: 1rem;
            min-height: 142px;
            margin-bottom: 0.75rem;
        }
        .bri-video-card h4 {
            margin: 0.7rem 0 0.45rem 0;
            font-size: 1rem;
        }
        .bri-video-card p {
            color: #a0a0a0 !important;
            font-size: 0.85rem;
        }
        .bri-video-status {
            display: inline-flex;
            border: 1px solid;
            border-radius: 999px;
            padding: 0.2rem 0.55rem;
            font-size: 0.74rem;
            text-transform: uppercase;
            letter-spacing: 0.08em;
            font-weight: 700;
        }
        .stProgress > div > div > div > div {
            background: linear-gradient(90deg, #40E0D0, #BA68C8);
        }
        .bri-sidebar-readiness {
            display: grid;
            gap: 0.4rem;
            padding: 0.8rem;
            border: 1px solid #333333;
            border-radius: 14px;
            background: #202020;
            font-size: 0.85rem;
        }
        @media (max-width: 900px) {
            .bri-hero, .bri-system-panel { grid-template-columns: 1fr; }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
