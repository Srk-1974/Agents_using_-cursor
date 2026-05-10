"""PyQt5 GUI and worker thread orchestration."""

from __future__ import annotations

from typing import Dict

from PyQt5.QtCore import QThread, pyqtSignal
from PyQt5.QtWidgets import (
    QApplication,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from agents.agent_orchestrator import AgentOrchestrator
from config import Settings


STATUS_COLORS = {
    "Idle": "#94a3b8",
    "Running": "#f59e0b",
    "Complete": "#22c55e",
    "Error": "#f43f5e",
}


class OrchestratorWorker(QThread):
    status_updated = pyqtSignal(str, str, str)
    finished_with_result = pyqtSignal(object)
    failed = pyqtSignal(str)

    def __init__(self, orchestrator: AgentOrchestrator, topic: str):
        super().__init__()
        self.orchestrator = orchestrator
        self.topic = topic

    def run(self) -> None:
        try:
            result = self.orchestrator.run(topic=self.topic, status_callback=self._emit_status)
            self.finished_with_result.emit(result)
        except Exception as error:  # noqa: BLE001
            self.failed.emit(str(error))

    def _emit_status(self, agent_name: str, status: str, message: str) -> None:
        self.status_updated.emit(agent_name, status, message)


class MainWindow(QMainWindow):
    def __init__(self, orchestrator: AgentOrchestrator):
        super().__init__()
        self.settings = Settings.from_env()
        self.orchestrator = orchestrator
        self.worker: OrchestratorWorker | None = None
        self.agent_status_labels: Dict[str, QLabel] = {}
        self._build_ui()

    def _build_ui(self) -> None:
        self.setWindowTitle("Multi-Agent AI Console")
        self.resize(1000, 700)

        root_widget = QWidget()
        root_layout = QVBoxLayout(root_widget)
        root_layout.setSpacing(14)

        title = QLabel("Multi-Agent AI Workflow Studio")
        subtitle = QLabel("Run LinkedIn publishing and YouTube research in one coordinated workflow.")
        title.setObjectName("titleLabel")
        subtitle.setObjectName("subtitleLabel")

        top_row = QHBoxLayout()
        self.topic_input = QLineEdit()
        self.topic_input.setPlaceholderText("Enter a topic (e.g., AI product strategy)...")
        self.run_button = QPushButton("Run Agents")
        self.run_button.clicked.connect(self._on_run_clicked)
        top_row.addWidget(self.topic_input)
        top_row.addWidget(self.run_button)

        panel_row = QHBoxLayout()
        panel_row.addWidget(self._build_agent_panel("linkedin", "Agent 1 - LinkedIn Publisher"))
        panel_row.addWidget(self._build_agent_panel("youtube", "Agent 2 - YouTube Researcher"))
        panel_row.addWidget(self._build_agent_panel("orchestrator", "Agent 3 - Orchestrator"))

        self.output_text = QTextEdit()
        self.output_text.setReadOnly(True)
        self.output_text.setPlaceholderText("Combined output will appear here...")

        self._apply_theme(root_widget)
        root_layout.addWidget(title)
        root_layout.addWidget(subtitle)
        root_layout.addLayout(top_row)
        root_layout.addLayout(panel_row)
        root_layout.addWidget(self.output_text)

        self.setCentralWidget(root_widget)
        self._set_all_statuses_idle()

    def _build_agent_panel(self, key: str, title: str) -> QGroupBox:
        group = QGroupBox(title)
        group.setObjectName("agentPanel")
        layout = QVBoxLayout(group)
        status = QLabel()
        status.setText("● Idle")
        status.setObjectName("statusChip")
        status.setStyleSheet(
            f"font-weight: 600; color: #e2e8f0; background-color: {STATUS_COLORS['Idle']};"
            "padding: 8px 12px; border-radius: 10px;"
        )
        layout.addWidget(status)
        self.agent_status_labels[key] = status
        return group

    def _set_all_statuses_idle(self) -> None:
        for key in self.agent_status_labels:
            self._set_status(key, "Idle", "Waiting")

    def _set_status(self, agent_name: str, status: str, message: str) -> None:
        label = self.agent_status_labels.get(agent_name)
        if not label:
            return
        color = STATUS_COLORS.get(status, STATUS_COLORS["Idle"])
        label.setText(f"{status} - {message}")
        label.setStyleSheet(
            f"font-weight: 600; color: #e2e8f0; background-color: {color};"
            "padding: 8px 12px; border-radius: 10px;"
        )

    def _apply_theme(self, widget: QWidget) -> None:
        widget.setStyleSheet(
            """
            QWidget {
                background-color: #0f172a;
                color: #e2e8f0;
                font-family: "Segoe UI", Arial, sans-serif;
                font-size: 13px;
            }
            #titleLabel {
                font-size: 26px;
                font-weight: 700;
                color: #f8fafc;
            }
            #subtitleLabel {
                color: #94a3b8;
                font-size: 13px;
                margin-bottom: 4px;
            }
            QLineEdit {
                background-color: #1e293b;
                border: 1px solid #334155;
                border-radius: 10px;
                padding: 10px 12px;
                color: #e2e8f0;
            }
            QLineEdit:focus {
                border: 1px solid #38bdf8;
            }
            QPushButton {
                background-color: #2563eb;
                border: none;
                border-radius: 10px;
                color: white;
                font-weight: 600;
                padding: 10px 18px;
                min-width: 130px;
            }
            QPushButton:hover {
                background-color: #1d4ed8;
            }
            QPushButton:disabled {
                background-color: #334155;
                color: #94a3b8;
            }
            QGroupBox#agentPanel {
                border: 1px solid #334155;
                border-radius: 14px;
                margin-top: 12px;
                padding: 12px;
                background-color: #111827;
            }
            QGroupBox#agentPanel::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 6px;
                color: #cbd5e1;
                font-weight: 600;
            }
            QTextEdit {
                background-color: #111827;
                border: 1px solid #334155;
                border-radius: 14px;
                padding: 12px;
                color: #e2e8f0;
                selection-background-color: #2563eb;
            }
            """
        )

    def _on_run_clicked(self) -> None:
        topic = self.topic_input.text().strip()
        if not topic:
            QMessageBox.warning(self, "Input Required", "Please enter a topic before running agents.")
            return

        self.run_button.setEnabled(False)
        self.output_text.clear()
        self._set_all_statuses_idle()

        self.worker = OrchestratorWorker(self.orchestrator, topic)
        self.worker.status_updated.connect(self._set_status)
        self.worker.finished_with_result.connect(self._on_finished)
        self.worker.failed.connect(self._on_failed)
        self.worker.start()

    def _on_finished(self, result: dict) -> None:
        self.run_button.setEnabled(True)
        self.output_text.setPlainText(self._render_result(result))

    def _on_failed(self, error_message: str) -> None:
        self.run_button.setEnabled(True)
        self._set_status("orchestrator", "Error", error_message)
        QMessageBox.critical(self, "Workflow Error", error_message)

    def _render_result(self, result: dict) -> str:
        linkedin = result.get("linkedin")
        youtube = result.get("youtube")
        lines = [f"Topic: {result.get('topic', '')}", ""]

        lines.append("=== LinkedIn Result ===")
        if linkedin:
            lines.append(f"Success: {linkedin.success}")
            lines.append(f"Message: {linkedin.message}")
            if linkedin.post_url:
                lines.append(f"Post URL: {linkedin.post_url}")
            lines.append("")
            lines.append("Generated Post Content:")
            lines.append(linkedin.content)
        else:
            lines.append("No LinkedIn result available.")

        lines.append("")
        lines.append("=== YouTube Research Report ===")
        if youtube and youtube.videos:
            lines.append(f"Message: {youtube.message}")
            for index, video in enumerate(youtube.videos, start=1):
                lines.append("")
                lines.append(f"{index}. {video.title}")
                lines.append(f"   Channel: {video.channel}")
                lines.append(f"   Views: {video.views:,}")
                lines.append(f"   URL: {video.url}")
                summary = (video.description[:220] + "...") if len(video.description) > 220 else video.description
                lines.append(f"   Summary: {summary}")
        elif youtube:
            lines.append(youtube.message)
        else:
            lines.append("No YouTube result available.")

        if result.get("errors"):
            lines.append("")
            lines.append("=== Errors ===")
            lines.extend(result["errors"])

        return "\n".join(lines)


def launch_app(orchestrator: AgentOrchestrator) -> None:
    app = QApplication([])
    window = MainWindow(orchestrator)
    window.show()
    app.exec_()
