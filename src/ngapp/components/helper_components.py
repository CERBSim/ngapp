# pylint: disable=protected-access """Basic components for webapp frontend."""
import datetime
import subprocess
import tempfile
from pathlib import Path
from typing import Callable, Literal

from .. import api
from ..utils import (
    Job,
    confirm,
    copy_simulation,
    is_pyodide,
    load_simulation,
    new_simulation,
    set_directory,
    temp_dir_with_files,
)
from .basecomponent import (
    Component,
    Event,
    get_component,
)  # needed from frontend:
from .qcomponents import (
    QBtn,
    QCard,
    QCardActions,
    QCardSection,
    QDialog,
    QFile,
    QIcon,
    QImg,
    QInput,
    QSpace,
    QTable,
    QTd,
    QTh,
    QToolbar,
    QToolbarTitle,
    QTooltip,
    QTr,
)


class Col(Component):
    def __init__(self, *children: Component | str, **kwargs):
        ui_class = kwargs.pop("ui_class", "")
        ui_class = f"col {ui_class}"
        super().__init__("div", *children, ui_class=ui_class, **kwargs)


class Row(Component):
    def __init__(self, *children: Component | str, **kwargs):
        ui_class = kwargs.pop("ui_class", "")
        ui_class = f"row {ui_class}"
        super().__init__("div", *children, ui_class=ui_class, **kwargs)


class Div(Component):
    def __init__(self, *children: Component | str, **kwargs):
        super().__init__("div", *children, **kwargs)


class Br(Component):
    def __init__(self, *children: Component | str, **kwargs):
        super().__init__("br", *children, **kwargs)


class Label(Component):
    def __init__(self, text="", **kwargs):
        super().__init__("span", **kwargs)
        self.ui_children = [text]
        self._props["text"] = text
        self.on_load(self._on_load)

    def _on_load(self):
        self.ui_children = [self.text]

    @property
    def text(self):
        return self._props["text"]

    @text.setter
    def text(self, value):
        self.ui_children = [value]
        self._set_prop("text", value)


class Centered(Component):
    """Create a div with centered content"""

    def __init__(self, *children: Component | str, **kwargs):
        ui_class = kwargs.pop("ui_class", "")
        ui_class = f"column items-center transparent {ui_class}"
        super().__init__("div", *children, ui_class=ui_class, **kwargs)


class Heading(Component):
    def __init__(self, text, level=2, **kwargs):
        ui_class = "text-h" + str(level) + " " + kwargs.pop("ui_class", "")
        super().__init__("div", text, ui_class=ui_class, **kwargs)


class NumberInput(QInput):
    """Thin wrapper for QInput with type='number' and model_value returning float"""

    def __init__(
        self, *children, ui_class=["q-mx-xs"], ui_step="any", **kwargs
    ):
        super().__init__(
            *children, ui_type="number", ui_class=ui_class, **kwargs
        )
        self._props["step"] = ui_step

    @QInput.ui_model_value.getter
    def ui_model_value(self) -> float | None:
        val = super().ui_model_value
        return None if (val is None or val == "") else float(val)


class FileName(QInput):
    """
    Helper to set simulation file name based on input. No input will set name to 'Untitled'.

    Args:
        app: The app instance
        ui_label: The label for the input
        ui_borderless: Use 'borderless' design for the input
    """

    def __init__(
        self,
        app=None,
        ui_label="Filename",
        ui_borderless=True,
        compute_filename: Callable | None = None,
        **kwargs,
    ):
        if app is None:
            raise ValueError("App is required")
        self.app = app
        super().__init__(
            ui_label=ui_label, ui_borderless=ui_borderless, **kwargs
        )
        self.on_update_model_value(self._on_update_model_value)
        self.on_load(self._on_load)
        self.on_before_save(self._on_before_save)
        compute_filename = compute_filename or (lambda: self.ui_model_value)
        self._compute_filename = compute_filename

    def _on_update_model_value(self):
        self.app.name = self._compute_filename()

    def _on_load(self):
        self.ui_model_value = self.app.name
        self.ui_model_value = self._compute_filename()

    def _on_before_save(self):
        self.ui_model_value = self._compute_filename()
        self.app.name = self.ui_model_value


class UserWarning(QDialog):
    def __init__(self, ui_title, ui_message, **kwargs):
        self.ui_heading = QCardSection(Heading(ui_title, 6))
        self._title = ui_title
        self.content = QCardSection(ui_message, ui_class="q-pt-none")
        self._message = ui_message
        card = QCard(
            self.ui_heading,
            self.content,
            QCardActions(
                QBtn(ui_flat=True, ui_label="Ok", ui_color="primary").on_click(
                    self.ui_hide
                ),
                ui_align="right",
            ),
        )
        super().__init__(card, **kwargs)

    @property
    def ui_title(self):
        return self._title

    @ui_title.setter
    def ui_title(self, value):
        self.ui_heading.ui_children = [Heading(value, 6)]
        self._title = value

    @property
    def ui_message(self):
        return self._message

    @ui_message.setter
    def ui_message(self, value):
        self.content.ui_children = [value]
        self._message = value


class FileUpload(QFile):
    def __init__(
        self,
        id="",
        ui_error_title="Error in File Upload",
        ui_error_message="Please upload a valid file",
        **kwargs,
    ):
        style = {
            "height": "100px",
            "border": "1px solid rgba(60, 190, 242, 1)",
            "border-radius": "15px",
            "background-color": "rgba(60, 190, 242, .2)",
            "margin-top": "30px",
            "margin-bottom": "70px",
            "padding": "20px",
            "border-style": "dashed",
            "max-width": "400px",
        }
        user_style = kwargs.pop("ui_style", {})
        if isinstance(user_style, str):
            user_style = {
                key: val
                for key, val in (
                    s.split(":") for s in user_style.split(";") if ":" in s
                )
            }
        style.update(user_style)
        super().__init__(id=id, ui_style=style, **kwargs)
        self.user_warning = UserWarning(
            ui_title=ui_error_title, ui_message=ui_error_message
        )
        self.slot_prepend = [QIcon(ui_name="upload"), self.user_warning]
        self.on_update_model_value(self.read_file)
        self.on_clear(self.clear_file)
        self.filename = None
        self.on_rejected(self.user_warning.ui_show)

    def clear_file(self):
        self.filename = None
        self.display_value = self.filename

    def read_file(self, event: Event):
        value = event.value

        if self.ui_multiple:
            self.filename = [file.name for file in value]
            self.display_value = ", ".join(self.filename)

            for file in value:
                self.storage.set(file.name, file.arrayBuffer())
        else:
            self.filename = value.name
            self.display_value = self.filename
            print("set storage", value.name)
            self.storage.set(value.name, value.arrayBuffer())

    def dump(self):
        data = (super().dump() or {}) | {"filename": self.filename}
        if "model-value" in data:
            data.pop("model-value")
        return data

    def load(self, data):
        if data is not None:
            self.filename = data.pop("filename")
            self.display_value = self.filename
        super().load(data)

    def on_file_loaded(self, handler: Callable):
        self.on("file_loaded", handler)

    @property
    def as_temporary_file(self) -> Path:
        """Returns a context manager with a temporary file on disk"""

        if self.ui_multiple:
            raise ValueError(
                "Multiple files cannot be saved as temporary file."
            )

        return temp_dir_with_files(
            {self.filename: self.storage.get(self.filename)}, return_list=False
        )

    def as_temporary_directory(self, extract_zip=False):
        """Returns a context manager that creates a temporary directory with all files.
        The context manager returns a list of file paths."""

        if self.ui_multiple:
            return temp_dir_with_files(
                {
                    filename: self.storage.get(filename)
                    for filename in self.filename
                },
                extract_zip=extract_zip,
            )
        return temp_dir_with_files(
            {self.filename: self.storage.get(self.filename)},
            extract_zip=extract_zip,
            return_list=False,
        )


class FileDownload(QBtn):
    def __init__(self, *children, id, **kwargs):
        """A button that downloads a file on click.

        The file can be set with set_file(filename, file_data=None, file_location=None).

        The file data is stored in the storage of the app and only retrieved when the button is clicked.
        """
        super().__init__(*children, id=id, **kwargs)
        self._filename = None
        self.ui_disable = True
        self.on("click", self.download)

    def set_file(self, filename, file_data=None, file_location=None):
        """Set the file to be downloaded on button click as file with name filename.

        If file_data is set, it is used as file content, otherwise the file is read from file_location. If no file location is given as well, the file is read from the current directory with the given filename.
        """
        assert (
            file_data is None or file_location is None
        ), "Only file data or file location can be set"
        self._filename = filename
        if file_data is not None:
            self.storage.set("file", file_data)
        else:
            if file_location is None:
                file_location = filename
            with open(file_location, "rb") as f:
                file_data = f.read()
                self.storage.set("file", file_data)
        self.ui_disable = False

        if not is_pyodide():
            self.storage.save()
            self._update_frontend()

    def download(self):
        if self._filename is not None:
            result = self.storage.get("file")
            self.download_file(data=result, filename=self._filename)

    def dump(self):
        return (super().dump() or {}) | {"filename": self._filename}

    def load(self, data):
        self._filename = data.pop("filename", None)
        self.ui_disable = self._filename == None
        super().load(data)


class JsonEditor(Component):
    def __init__(
        self, data: dict | None = None, options={"mode": "tree"}, **kwargs
    ):
        self._data = data or {}
        super().__init__("JsonEditorComponent", **kwargs)
        self._props["options"] = options
        self.on("_change", self._on_change)

    @property
    def data(self):
        return self._data

    @data.setter
    def data(self, value):
        self._data = value
        self._update_frontend(value, "set")

    def _on_change(self, event):
        self._data = event.value


class Table(QTable):
    """Wrapper class around QTable that allows to pass a list of lists as rows and disables pagination by default"""

    def __init__(
        self,
        ui_title="",
        ui_rows=[],
        ui_header=None,
        ui_align=None,
        ui_hide_bottom=True,
        ui_pagination={"rowsPerPage": 0},
        ui_hide_pagination=True,
        ui_style="min-width:400px;margin-bottom:50px;",
        **kwargs,
    ):
        columns = []
        if ui_header:
            for i in range(len(ui_header)):
                columns.append(
                    {
                        "name": f"col{i}",
                        "label": ui_header[i],
                        "field": f"col{i}",
                    }
                )
        else:
            for i in range(len(ui_rows[0])):
                columns.append(
                    {"name": f"col{i}", "label": "", "field": f"col{i}"}
                )
        if ui_align:
            alignments = {"l": "left", "c": "center", "r": "right"}
            for i, a in enumerate(ui_align):
                columns[i]["align"] = alignments[a]
        qrows = []
        for i, row in enumerate(ui_rows):
            entry = {"col" + str(j): row[j] for j in range(len(row))}
            entry["id"] = str(i)
            qrows.append(entry)

        super().__init__(
            ui_title=ui_title,
            ui_rows=self._convert_rows(ui_rows),
            ui_columns=columns,
            ui_hide_bottom=ui_hide_bottom,
            ui_pagination=ui_pagination,
            ui_hide_pagination=ui_hide_pagination,
            ui_style=ui_style,
            **kwargs,
        )

    def _convert_rows(self, rows):
        if len(rows) == 0 or isinstance(rows[0], dict):
            return rows
        qrows = []
        for i, row in enumerate(rows):
            entry = {"col" + str(j): row[j] for j in range(len(row))}
            entry["id"] = str(i)
            qrows.append(entry)
        return qrows

    @QTable.ui_rows.setter
    def ui_rows(self, value):
        self._set_prop("rows", self._convert_rows(value))

    def get_markdown(self):
        """Get the table as markdown"""
        rows = self.ui_rows
        header = (
            "| " + " | ".join([col["label"] for col in self.ui_columns]) + " |"
        )
        separator = "|" + "|".join(["---"] * len(self.ui_columns)) + "|"
        body = ""
        for row in rows:
            for col in self.ui_columns:
                value = row[col["name"]]
                body += "| " + str(value) + " "
            body += "|\n"
        return "\n".join([header, separator, body])


class JobComponent(QBtn):
    """
    A button to start and stop a job and monitor its status.

    :param id: Compoent id
    :param compute_function: Function that is called with compute_node
    """

    def __init__(
        self,
        id: str,
        compute_function: Callable,
        *args,
        **kwargs,
    ):
        self.compute_function: Callable = compute_function
        self.tooltip = QTooltip("Start job", id=f"{id}_tooltip")
        super().__init__(self.tooltip, id=id, **kwargs)
        self._set_prop("icon", "mdi-play")
        self.job_status: dict = {}
        self.job: Job | None = None
        self.on("click", self._on_click)
        self.on("load", self.update_job_status)

    @property
    def job_id(self):
        if self.job is not None:
            return self.job.id
        return None

    def set_job_from_id(self, job_id: int):
        self.job = Job(**{"id": job_id})

    def _on_click(self):
        if not self.job_status.get("status") in ["started", "queued"]:
            self._start_job()
        else:
            confirm(
                "Abort Calculation",
                "Are you sure you want to abort the calculation?",
                on_ok=self._stop_job,
            )

    def _start_job(self):
        self.progress = 0.0
        self.job = self.compute_function(_job_component=self)
        self.update_job_status()
        self._handle("start")

    def _stop_job(self):
        self.update_job_status()
        if self.job_status.get("status") in ["started", "queued"]:
            try:
                self.job.abort()
                self.update_job_status()
                self._reset_button()
                print("stop")
                self._handle("stop")
            except Exception as e:
                print(f"Error stopping job: {e}")
        else:
            # workaround for the case where the job is already finished until
            # https://github.com/rq/rq/issues/1631 is fixed
            self._start_job()

    def _update_button(self):
        print("update job status", self.job_status.get("status"))
        if self.job_status.get("status") in ["started", "queued"]:
            self.tooltip.ui_children = [f"Abort"]
            self._set_prop("icon", "mdi-stop")
        else:
            self.tooltip.ui_children = ["Run"]
            self._set_prop("icon", "mdi-play")
        self.tooltip.ui_model_value = False

    @property
    def progress(self):
        return self.job_status.get("progress", 0.0)

    @progress.setter
    def progress(self, value):
        self.job_status["progress"] = value
        self._update_button()

    def update_job_status(self):
        if self.job is not None:
            self.job_status.update(self.job.get_status())
            self._update_button()

    def _reset_button(self):
        self.tooltip.ui_children = ["Start job"]
        self._set_prop("icon", "mdi-play")

    def dump(self):
        data = (super().dump() or {}) | {"job_status": self.job_status}
        if self.job is not None:
            data["job"] = self.job.model_dump()
        return data

    def load(self, data):
        self.job_status = data.pop("job_status", {})
        job = data.pop("job", None)
        if job is not None:
            self.job = Job(**job)
        super().load(data)

    def on_stop(self, handler: Callable):
        """Set the function to be called when the job is stopped."""
        self.on("stop", handler)

    def on_start(self, handler: Callable):
        """Set the function to be called when the job is started."""
        self.on("start", handler)


class NewSimulationButton(QBtn):
    """Helper class to create a new simulation"""

    def __init__(
        self,
        ui_tooltip="New",
        ui_icon="mdi-file-plus",
        ui_flat=True,
        *args,
        **kwargs,
    ):
        super().__init__(
            QTooltip(ui_tooltip),
            ui_icon=ui_icon,
            ui_flat=ui_flat,
            *args,
            **kwargs,
        )
        self.on("click", new_simulation)


class LoadSimulationButton(QBtn):
    """Helper class to run a simulation"""

    def __init__(
        self,
        app,
        ui_tooltip="Load",
        ui_icon="mdi-folder-open",
        ui_flat=True,
        *args,
        **kwargs,
    ):
        super().__init__(
            QTooltip(ui_tooltip),
            ui_icon=ui_icon,
            ui_flat=ui_flat,
            *args,
            **kwargs,
        )
        self.app = app
        self.load_dialog = LoadDialog(app=self.app)
        self.on("click", self.load_dialog.ui_show)
        self.ui_children = [self.load_dialog, *self.ui_children]


class SaveSimulationButton(QBtn):
    """Helper class to save a simulation"""

    def __init__(
        self,
        app,
        ui_tooltip="Save",
        ui_icon="mdi-content-save",
        ui_flat=True,
        *args,
        **kwargs,
    ):
        super().__init__(
            QTooltip(ui_tooltip),
            ui_icon=ui_icon,
            ui_flat=ui_flat,
            *args,
            **kwargs,
        )
        self.app = app
        self.on("click", self.app.save)


class CopySimulationButton(QBtn):
    """Helper class to copy a simulation"""

    def __init__(
        self,
        app,
        ui_tooltip="Copy",
        ui_icon="mdi-content-copy",
        ui_flat=True,
        *args,
        **kwargs,
    ):
        super().__init__(
            QTooltip(ui_tooltip),
            ui_icon=ui_icon,
            ui_flat=ui_flat,
            *args,
            **kwargs,
        )
        self.app = app
        self.on("click", self.__on_click)

    def __on_click(self):
        data = self.app.dump()
        name = data["metadata"].get("name", "")
        if name:
            name += " (copy)"
        data["metadata"]["name"] = name
        copy_simulation(data)


class RunSimulationButton(QBtn):
    """Helper class to run a simulation"""

    def __init__(
        self,
        run_function: Callable,
        ui_tooltip="Run",
        ui_icon="mdi-play",
        ui_flat=True,
        *args,
        **kwargs,
    ):
        super().__init__(
            QTooltip(ui_tooltip),
            ui_icon=ui_icon,
            ui_flat=ui_flat,
            *args,
            **kwargs,
        )
        self.on("click", run_function)


class SimulationTable(QTable):
    """A table to display simulations from the server, if no dialog is given, the rows must be set manually"""

    def __init__(self, dialog=None):
        super().__init__(
            ui_title="Load Simulation",
            ui_pagination={"rowsPerPage": 5},
            ui_columns=[
                {"name": "index", "label": "Index", "field": "index"},
                {"name": "id", "label": "ID", "field": "id"},
                {"name": "name", "label": "Name", "field": "name"},
                {"name": "created", "label": "Created", "field": "created"},
                {"name": "modified", "label": "Modified", "field": "modified"},
                {"name": "status", "label": "Status", "field": "status"},
            ],
            ui_visible_columns=["name", "created", "modified", "status"],
            ui_style="padding:20px;min-width:850px;",
        )
        self.ui_slot_header = [
            QTr(
                QTh("Name"),
                QTh("Created"),
                QTh("Modified"),
                QTh("Status"),
                QTh("Actions"),
                ui_style="position:sticky;top:0;z-index:1;background-color:white;",
            )
        ]
        self.ui_slot_body = self.create_row
        self.ui_dialog = dialog

    def _load_simulation(self, event: Event):
        file_id = event.arg["file_id"]
        load_simulation(file_id)
        if self.ui_dialog:
            self.ui_dialog.ui_hide()
            self.ui_dialog.app.load(api.get(f"/model/{file_id}"))

    def _delete_simulation(self, event: Event):
        file_id = event.arg["file_id"]
        api.delete(f"/files/{file_id}")
        self.ui_rows = [r for r in self.ui_rows if r["id"] != file_id]

    def create_row(self, props):
        row = props["row"]
        created = datetime.datetime.fromtimestamp(row["created"]).strftime(
            "%Y-%m-%d %H:%M:%S"
        )
        modified = datetime.datetime.fromtimestamp(row["modified"]).strftime(
            "%Y-%m-%d %H:%M:%S"
        )
        load_btn = QBtn(
            QTooltip("Load"), ui_icon="mdi-folder-open", ui_flat=True
        )
        load_btn.on_click(self._load_simulation, arg={"file_id": row["id"]})
        delete_btn = QBtn(
            QTooltip("Delete"),
            ui_icon="delete",
            ui_color="negative",
            ui_flat=True,
        )
        delete_btn.on_click(self._delete_simulation, arg={"file_id": row["id"]})
        status = row["status"]
        name, create, modified = QTd(row["name"]), QTd(created), QTd(modified)
        row_comp = QTr(
            name, create, modified, QTd(status), QTd(load_btn, delete_btn)
        )
        row_comp.on(
            "dblclick", self._load_simulation, arg={"file_id": row["id"]}
        )
        return [row_comp]


class LoadDialog(QDialog):
    """A dialog to load simulations from the server"""

    def __init__(self, app, *args, **kwargs):
        self.app = app
        self.simulations = SimulationTable(dialog=self)
        super().__init__(self.simulations, *args, **kwargs)

    def ui_show(self):
        super().ui_show()
        sims = api.get(f"/simulations/{self.app.metadata['app_id']}")
        jobs = api.get(f"/job/by_app/{self.app.metadata['app_id']}/status")
        jobs = {job["file_id"]: job for job in jobs}
        job_status = {
            -1: "No job",
            0: "Created",
            1: "Running",
            2: "Finished",
            3: "Failed",
            4: "Stopped",
        }
        for i, s in enumerate(sims):
            s["index"] = i
            job = jobs.get(s["id"], {"status": -1})
            s["status"] = job_status.get(job["status"])
        sims = sorted(sims, key=lambda x: x["modified"], reverse=True)
        self.simulations.ui_rows = sims


class ToolBar(QToolbar):
    """A toolbar with a logo, app name, filename input, new, load, save and run buttons"""

    def __init__(
        self,
        app,
        ui_class="bg-grey-5 text-white",
        logo: str | None = None,
        app_name: str | None = None,
        filename: FileName | None = None,
        buttons: list[Component] = [],
        *args,
        **kwargs,
    ):
        self.app = app
        components = []
        if logo:
            components.append(
                QImg(ui_src=logo, ui_style="height:35px; width:35px;")
            )
            self.logo = components[-1]
        else:
            self.logo = None
        if app_name:
            components.append(QToolbarTitle(app_name, ui_shrink=True))
            self.title = components[-1]
        else:
            self.title = None
        components.append(QSpace())
        if filename:
            components.append(filename)
        components.append(QSpace())
        for button in buttons:
            components.append(button)
        super().__init__(*components, ui_class=ui_class, *args, **kwargs)


class Rules:
    @staticmethod
    def range(min_: float, max_: float):
        return (
            lambda value: value is not None
            and min_ <= value <= max_
            or f"Value must be between {min_} and {max_}"
        )

    @staticmethod
    def less_than(limit: float):
        return (
            lambda value: value is not None
            and value < limit
            or f"Value must be less than {limit}"
        )

    @staticmethod
    def greater_than(limit: float):
        return (
            lambda value: value is not None
            and value > limit
            or f"Value must be greater than {limit}"
        )

    @staticmethod
    def at_least(limit: float):
        return (
            lambda value: value is not None
            and value >= limit
            or f"Value must be at least {limit}"
        )

    @staticmethod
    def at_most(limit: float):
        return (
            lambda value: value is not None
            and value <= limit
            or f"Value must be at most {limit}"
        )

    positive = (
        lambda value: value is not None
        and value > 0
        or "Value must be positive"
    )
    negative = (
        lambda value: value is not None
        and value < 0
        or "Value must be negative"
    )
    required = (
        lambda value: value is not None and value != "" or "Value is required"
    )


class Report(QBtn):
    """A button that generates a pdf report from a specified format (docx, md)"""

    def __init__(
        self,
        app,
        id,
        ui_tooltip="Report",
        ui_icon="mdi-file-document",
        ui_flat=True,
        ui_disable=True,
        *args,
        **kwargs,
    ):
        super().__init__(
            QTooltip(ui_tooltip),
            ui_icon=ui_icon,
            ui_flat=ui_flat,
            ui_disable=ui_disable,
            id=id,
            *args,
            **kwargs,
        )
        self.app = app
        self._filename = None
        self.on("click", self.download)

    def _convert_and_set_report(
        self,
        input_file: Path,
        output_file: Path,
    ):
        command = ["pandoc", input_file, "-o", output_file]
        if input_file.name.endswith(".md"):
            command.append("--pdf-engine=xelatex")
        subprocess.run(command)
        self._set_report(
            filename=output_file.name, file_data=output_file.read_bytes()
        )

    def _generate_docx_report(
        self,
        template_path: Path,
        pdf_file: Path,
        context: dict,
        files: dict[str, str | bytes] = {},
    ):
        from docxtpl import DocxTemplate, InlineImage

        docx_file = pdf_file.with_suffix(".docx")
        template = DocxTemplate(template_path)
        for key, value in files.items():
            context[key] = InlineImage(template, value)
        template.render(context)
        template.save(docx_file)
        self._convert_and_set_report(docx_file, pdf_file)

    def _generate_md_report(
        self,
        template_path: Path,
        pdf_file: Path,
        context: dict,
        files: dict[str, str | bytes],
    ):
        from jinja2 import Template

        for name, data in files.items():
            file_path = Path(name)
            if isinstance(data, str):
                file_path.write_text(data, encoding="utf-8")
            else:
                file_path.write_bytes(data)
        md_file = pdf_file.with_suffix(".md")
        template = Template(template_path.read_bytes().decode("utf-8"))
        md_file.write_text(template.render(context), encoding="utf-8")
        self._convert_and_set_report(md_file, pdf_file)

    def generate_report(
        self,
        template_file: Path | str,
        context: dict,
        output_file: Path | str,
        files: dict[str, str | bytes],
        file_type=Literal["md", "docx"] | None,
    ):
        output_file = Path(output_file)
        template_file = Path(template_file)
        if template_file.name.endswith(".docx"):
            file_type = file_type or "docx"
        if template_file.name.endswith(".md"):
            file_type = file_type or "md"

        if file_type not in ["md", "docx"]:
            raise ValueError(f"Invalid file_type: {file_type}")

        with tempfile.TemporaryDirectory() as temp_dir:
            with set_directory(temp_dir):
                template_path = self._status.app.assets_path / template_file
                if file_type == "md":
                    self._generate_md_report(
                        template_path=template_path,
                        pdf_file=output_file,
                        context=context,
                        files=files,
                    )
                elif file_type == "docx":
                    self._generate_docx_report(
                        template_path=template_path,
                        pdf_file=output_file,
                        context=context,
                        files=files,
                    )

    def create_report(
        self,
        filename,
        file_type: Literal["md", "docx"],
        template_path: str,
    ):
        """
        Create a report in the specified format.

        Args:
            filename (str): The name of the report file.
            file_type (Literal["md", "docx"]): The format of the report file.
            template_path (str): The path to the template file. Needs to be in assets folder.
        Raises:
            ValueError: If the file type is not supported.
        """
        template_path = self._status.app.assets_path / template_path
        if file_type == "md":
            self._generate_md_report(
                pdf_file=filename, template_path=template_path
            )
        elif file_type == "docx":
            self._generate_docx_report(
                pdf_file=filename, template_path=template_path
            )
        else:
            raise ValueError(f"Unsupported report type: {file_type}")

    def _set_report(self, filename: str, file_data: bytes):
        """Set the file to be downloaded on button click as file with name filename."""
        self._filename = filename
        self.storage.set("report", file_data)
        self.ui_disable = False
        if not is_pyodide():
            self.storage.save()
            self._update_frontend()

    def download(self):
        if self._filename is not None:
            report = self.storage.get("report")
            self.download_file(data=report, filename=self._filename)

    def dump(self):
        return (super().dump() or {}) | {"filename": self._filename}

    def load(self, data):
        self._filename = data.pop("filename", None)
        self.disable = self._filename == None
        super().load(data)
