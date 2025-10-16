"""Logging dashboard for BRI - Real-time log viewer and analytics."""

import streamlit as st
import os
import json
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict, Any
import re
from collections import Counter

from config import Config


class LogDashboard:
    """Dashboard for viewing and analyzing logs."""
    
    def __init__(self):
        """Initialize log dashboard."""
        self.log_dir = Config.LOG_DIR
        self.log_files = {
            'General': 'bri.log',
            'Errors': 'bri_errors.log',
            'Performance': 'bri_performance.log',
            'Audit': 'bri_audit.log',
            'Pipeline': 'bri_pipeline.log'
        }
    
    def render(self):
        """Render the logging dashboard."""
        st.title("📊 BRI Logging Dashboard")
        
        # Sidebar for filters
        with st.sidebar:
            st.header("Filters")
            
            # Log file selection
            selected_log = st.selectbox(
                "Log File",
                options=list(self.log_files.keys()),
                index=0
            )
            
            # Log level filter
            log_levels = st.multiselect(
                "Log Levels",
                options=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
                default=['INFO', 'WARNING', 'ERROR']
            )
            
            # Time range
            time_range = st.selectbox(
                "Time Range",
                options=['Last 1 hour', 'Last 6 hours', 'Last 24 hours', 'Last 7 days', 'All'],
                index=2
            )
            
            # Search
            search_query = st.text_input("Search", placeholder="video_id, error message, etc.")
            
            # Component filter
            component_filter = st.text_input("Component", placeholder="services.agent, tools.*, etc.")
            
            # Refresh button
            if st.button("🔄 Refresh", use_container_width=True):
                st.rerun()
        
        # Main content tabs
        tab1, tab2, tab3, tab4 = st.tabs([
            "📜 Log Viewer",
            "📈 Analytics",
            "⚡ Performance",
            "🔍 Error Tracking"
        ])
        
        with tab1:
            self._render_log_viewer(
                selected_log,
                log_levels,
                time_range,
                search_query,
                component_filter
            )
        
        with tab2:
            self._render_analytics(selected_log, time_range)
        
        with tab3:
            self._render_performance_metrics()
        
        with tab4:
            self._render_error_tracking()
    
    def _render_log_viewer(
        self,
        log_type: str,
        log_levels: List[str],
        time_range: str,
        search_query: str,
        component_filter: str
    ):
        """Render real-time log viewer."""
        st.subheader(f"📜 {log_type} Logs")
        
        # Get log file path
        log_file = os.path.join(self.log_dir, self.log_files[log_type])
        
        if not os.path.exists(log_file):
            st.warning(f"Log file not found: {log_file}")
            return
        
        # Read and filter logs
        logs = self._read_logs(log_file, time_range)
        filtered_logs = self._filter_logs(
            logs,
            log_levels,
            search_query,
            component_filter
        )
        
        # Display stats
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Lines", len(logs))
        with col2:
            st.metric("Filtered", len(filtered_logs))
        with col3:
            error_count = sum(1 for log in filtered_logs if 'ERROR' in log or 'CRITICAL' in log)
            st.metric("Errors", error_count)
        with col4:
            warning_count = sum(1 for log in filtered_logs if 'WARNING' in log)
            st.metric("Warnings", warning_count)
        
        # Display logs
        st.markdown("---")
        
        # Number of lines to show
        lines_to_show = st.slider("Lines to show", 10, 500, 100)
        
        # Show most recent logs
        recent_logs = filtered_logs[-lines_to_show:]
        
        # Display in code block with syntax highlighting
        log_text = "\n".join(recent_logs)
        st.code(log_text, language="log")
        
        # Download button
        st.download_button(
            label="📥 Download Filtered Logs",
            data=log_text,
            file_name=f"{log_type.lower()}_filtered_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log",
            mime="text/plain"
        )
    
    def _render_analytics(self, log_type: str, time_range: str):
        """Render log analytics."""
        st.subheader("📈 Log Analytics")
        
        log_file = os.path.join(self.log_dir, self.log_files[log_type])
        
        if not os.path.exists(log_file):
            st.warning(f"Log file not found: {log_file}")
            return
        
        logs = self._read_logs(log_file, time_range)
        
        # Parse logs for analytics
        log_levels = []
        components = []
        timestamps = []
        
        for log in logs:
            # Extract log level
            for level in ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']:
                if level in log:
                    log_levels.append(level)
                    break
            
            # Extract component (logger name)
            match = re.search(r' - ([a-zA-Z0-9_.]+) - ', log)
            if match:
                components.append(match.group(1))
            
            # Extract timestamp
            match = re.search(r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})', log)
            if match:
                try:
                    timestamps.append(datetime.strptime(match.group(1), '%Y-%m-%d %H:%M:%S'))
                except:
                    pass
        
        # Display analytics
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**Log Level Distribution**")
            if log_levels:
                level_counts = Counter(log_levels)
                for level, count in level_counts.most_common():
                    percentage = (count / len(log_levels)) * 100
                    st.write(f"{level}: {count} ({percentage:.1f}%)")
            else:
                st.write("No data")
        
        with col2:
            st.markdown("**Top Components**")
            if components:
                component_counts = Counter(components)
                for component, count in component_counts.most_common(10):
                    st.write(f"{component}: {count}")
            else:
                st.write("No data")
        
        # Timeline
        if timestamps:
            st.markdown("**Activity Timeline**")
            # Group by hour
            hour_counts = Counter([ts.replace(minute=0, second=0) for ts in timestamps])
            
            if hour_counts:
                hours = sorted(hour_counts.keys())
                counts = [hour_counts[h] for h in hours]
                
                st.line_chart(
                    data={
                        'Time': [h.strftime('%H:%M') for h in hours],
                        'Count': counts
                    },
                    x='Time',
                    y='Count'
                )
    
    def _render_performance_metrics(self):
        """Render performance metrics."""
        st.subheader("⚡ Performance Metrics")
        
        perf_log = os.path.join(self.log_dir, 'bri_performance.log')
        
        if not os.path.exists(perf_log):
            st.warning("Performance log not found")
            return
        
        logs = self._read_logs(perf_log, 'Last 24 hours')
        
        # Parse execution times
        execution_times = {}
        
        for log in logs:
            # Extract operation and time
            match = re.search(r'(\w+) completed in ([\d.]+)s', log)
            if match:
                operation = match.group(1)
                time_taken = float(match.group(2))
                
                if operation not in execution_times:
                    execution_times[operation] = []
                execution_times[operation].append(time_taken)
        
        if not execution_times:
            st.info("No performance data available")
            return
        
        # Display metrics
        for operation, times in sorted(execution_times.items()):
            with st.expander(f"📊 {operation}"):
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric("Count", len(times))
                with col2:
                    st.metric("Avg", f"{sum(times)/len(times):.3f}s")
                with col3:
                    st.metric("Min", f"{min(times):.3f}s")
                with col4:
                    st.metric("Max", f"{max(times):.3f}s")
                
                # Show distribution
                if len(times) > 1:
                    st.line_chart(times)
        
        # Cache metrics
        st.markdown("---")
        st.markdown("**Cache Performance**")
        
        cache_hits = sum(1 for log in logs if 'Cache HIT' in log)
        cache_misses = sum(1 for log in logs if 'Cache MISS' in log)
        total_cache = cache_hits + cache_misses
        
        if total_cache > 0:
            hit_rate = (cache_hits / total_cache) * 100
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Cache Hits", cache_hits)
            with col2:
                st.metric("Cache Misses", cache_misses)
            with col3:
                st.metric("Hit Rate", f"{hit_rate:.1f}%")
        else:
            st.info("No cache data available")
    
    def _render_error_tracking(self):
        """Render error tracking."""
        st.subheader("🔍 Error Tracking")
        
        error_log = os.path.join(self.log_dir, 'bri_errors.log')
        
        if not os.path.exists(error_log):
            st.warning("Error log not found")
            return
        
        logs = self._read_logs(error_log, 'Last 24 hours')
        
        if not logs:
            st.success("✅ No errors in the last 24 hours!")
            return
        
        # Group similar errors
        error_patterns = {}
        
        for log in logs:
            # Extract error message (simplified)
            match = re.search(r'ERROR.*? - (.+?)(?:\n|$)', log)
            if match:
                error_msg = match.group(1)
                # Normalize error message
                normalized = re.sub(r'\d+', 'N', error_msg)
                normalized = re.sub(r'[a-f0-9]{8,}', 'ID', normalized)
                
                if normalized not in error_patterns:
                    error_patterns[normalized] = {
                        'count': 0,
                        'examples': [],
                        'timestamps': []
                    }
                
                error_patterns[normalized]['count'] += 1
                if len(error_patterns[normalized]['examples']) < 3:
                    error_patterns[normalized]['examples'].append(error_msg)
                
                # Extract timestamp
                ts_match = re.search(r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})', log)
                if ts_match:
                    error_patterns[normalized]['timestamps'].append(ts_match.group(1))
        
        # Display error groups
        st.metric("Unique Error Types", len(error_patterns))
        st.metric("Total Errors", len(logs))
        
        st.markdown("---")
        
        # Sort by frequency
        sorted_errors = sorted(
            error_patterns.items(),
            key=lambda x: x[1]['count'],
            reverse=True
        )
        
        for i, (pattern, info) in enumerate(sorted_errors, 1):
            with st.expander(f"❌ Error #{i} - {info['count']} occurrences"):
                st.markdown(f"**Pattern:** `{pattern}`")
                
                st.markdown("**Examples:**")
                for example in info['examples']:
                    st.code(example, language="text")
                
                if info['timestamps']:
                    st.markdown(f"**First seen:** {info['timestamps'][0]}")
                    st.markdown(f"**Last seen:** {info['timestamps'][-1]}")
    
    def _read_logs(self, log_file: str, time_range: str) -> List[str]:
        """Read logs from file with time filtering.
        
        Args:
            log_file: Path to log file
            time_range: Time range filter
            
        Returns:
            List of log lines
        """
        if not os.path.exists(log_file):
            return []
        
        # Calculate cutoff time
        cutoff = None
        if time_range == 'Last 1 hour':
            cutoff = datetime.now() - timedelta(hours=1)
        elif time_range == 'Last 6 hours':
            cutoff = datetime.now() - timedelta(hours=6)
        elif time_range == 'Last 24 hours':
            cutoff = datetime.now() - timedelta(hours=24)
        elif time_range == 'Last 7 days':
            cutoff = datetime.now() - timedelta(days=7)
        
        # Read file
        try:
            with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()
            
            # Filter by time if needed
            if cutoff:
                filtered_lines = []
                for line in lines:
                    match = re.search(r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})', line)
                    if match:
                        try:
                            log_time = datetime.strptime(match.group(1), '%Y-%m-%d %H:%M:%S')
                            if log_time >= cutoff:
                                filtered_lines.append(line.rstrip())
                        except:
                            filtered_lines.append(line.rstrip())
                    else:
                        # Include lines without timestamp (continuation lines)
                        if filtered_lines:
                            filtered_lines.append(line.rstrip())
                
                return filtered_lines
            else:
                return [line.rstrip() for line in lines]
                
        except Exception as e:
            st.error(f"Error reading log file: {e}")
            return []
    
    def _filter_logs(
        self,
        logs: List[str],
        log_levels: List[str],
        search_query: str,
        component_filter: str
    ) -> List[str]:
        """Filter logs based on criteria.
        
        Args:
            logs: List of log lines
            log_levels: Log levels to include
            search_query: Search query
            component_filter: Component filter pattern
            
        Returns:
            Filtered log lines
        """
        filtered = []
        
        for log in logs:
            # Filter by log level
            if log_levels:
                if not any(level in log for level in log_levels):
                    continue
            
            # Filter by search query
            if search_query:
                if search_query.lower() not in log.lower():
                    continue
            
            # Filter by component
            if component_filter:
                if component_filter not in log:
                    continue
            
            filtered.append(log)
        
        return filtered


def render_logging_dashboard():
    """Render the logging dashboard page."""
    dashboard = LogDashboard()
    dashboard.render()


if __name__ == '__main__':
    render_logging_dashboard()
