
from PySide6 import QtWidgets, QtCore
import maya.cmds as cmds
import random
import math

class GrassClumpWindToolVaried(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Grass Clump + Wind Tool (Varied)")
        self.setMinimumSize(500, 350)
        self.build_ui()

    def build_ui(self):
        layout = QtWidgets.QVBoxLayout()

        target_layout = QtWidgets.QHBoxLayout()
        self.target_field = QtWidgets.QLineEdit()
        target_btn = QtWidgets.QPushButton("Select Grass Blade")
        target_btn.clicked.connect(self.select_target)
        target_layout.addWidget(self.target_field)
        target_layout.addWidget(target_btn)
        layout.addLayout(target_layout)

        plane_layout = QtWidgets.QHBoxLayout()
        self.plane_field = QtWidgets.QLineEdit()
        plane_btn = QtWidgets.QPushButton("Select Plane")
        plane_btn.clicked.connect(self.select_plane)
        plane_layout.addWidget(self.plane_field)
        plane_layout.addWidget(plane_btn)
        layout.addLayout(plane_layout)

        form_layout = QtWidgets.QFormLayout()
        self.count_spin = QtWidgets.QSpinBox()
        self.count_spin.setRange(1, 5000)
        self.count_spin.setValue(200)
        form_layout.addRow("Number of Blades:", self.count_spin)

        self.clump_spin = QtWidgets.QSpinBox()
        self.clump_spin.setRange(1, 50)
        self.clump_spin.setValue(5)
        form_layout.addRow("Blades per Clump:", self.clump_spin)

        self.scale_min_spin = QtWidgets.QDoubleSpinBox()
        self.scale_min_spin.setRange(0.01, 10.0)
        self.scale_min_spin.setValue(0.8)
        self.scale_max_spin = QtWidgets.QDoubleSpinBox()
        self.scale_max_spin.setRange(0.01, 10.0)
        self.scale_max_spin.setValue(1.2)
        form_layout.addRow("Random Scale Min:", self.scale_min_spin)
        form_layout.addRow("Random Scale Max:", self.scale_max_spin)

        layout.addLayout(form_layout)

        wind_group = QtWidgets.QGroupBox("Wind & Turbulence")
        wind_layout = QtWidgets.QFormLayout()
        self.wind_speed_slider = QtWidgets.QSlider(QtCore.Qt.Orientation.Horizontal)
        self.wind_speed_slider.setRange(1, 100)
        self.wind_speed_slider.setValue(20)
        wind_layout.addRow("Wind Speed:", self.wind_speed_slider)

        self.turbulence_slider = QtWidgets.QSlider(QtCore.Qt.Orientation.Horizontal)
        self.turbulence_slider.setRange(1, 50)
        self.turbulence_slider.setValue(10)
        wind_layout.addRow("Turbulence:", self.turbulence_slider)

        apply_wind_btn = QtWidgets.QPushButton("Apply Wind")
        apply_wind_btn.clicked.connect(self.apply_wind)
        wind_layout.addRow(apply_wind_btn)
        wind_group.setLayout(wind_layout)
        layout.addWidget(wind_group)

        scatter_btn = QtWidgets.QPushButton("Scatter Grass")
        scatter_btn.clicked.connect(self.scatter_grass)
        layout.addWidget(scatter_btn)

        self.setLayout(layout)

    def select_target(self):
        selection = cmds.ls(selection=True)
        if selection:
            self.target_field.setText(selection[0])

    def select_plane(self):
        selection = cmds.ls(selection=True)
        if selection:
            self.plane_field.setText(selection[0])

    def scatter_grass(self):
        target = self.target_field.text()
        plane = self.plane_field.text()

        if not target or not plane:
            cmds.warning("Select both grass blade and plane!")
            return

        count = self.count_spin.value()
        clump_size = self.clump_spin.value()
        scale_min = self.scale_min_spin.value()
        scale_max = self.scale_max_spin.value()

        if cmds.objExists("Grass_Scatter_Group"):
            cmds.delete("Grass_Scatter_Group")
        scatter_group = cmds.group(empty=True, name="Grass_Scatter_Group")

        bbox = cmds.exactWorldBoundingBox(plane)
        xmin, ymin, zmin, xmax, ymax, zmax = bbox

        num_clumps = max(1, count // clump_size)

        for c in range(num_clumps):
            cx = random.uniform(xmin, xmax)
            cz = random.uniform(zmin, zmax)
            cy = (ymin + ymax) / 2

            clump_group = cmds.group(empty=True, name=f"clump_{c}")
            cmds.parent(clump_group, scatter_group)

            for i in range(clump_size):
                dx = random.uniform(-0.2, 0.2)
                dz = random.uniform(-0.2, 0.2)
                x = cx + dx
                z = cz + dz
                y = cy

                blade = cmds.duplicate(target, name=f"{target}_blade_{c}_{i}", returnRootsOnly=True)[0]
                cmds.delete(blade, ch=True)
                for attr in ["translateX", "translateY", "translateZ",
                             "rotateX", "rotateY", "rotateZ",
                             "scaleX", "scaleY", "scaleZ"]:
                    cmds.setAttr(f"{blade}.{attr}", lock=False)

                ry_offset = random.uniform(-25, 25)
                rx_offset = random.uniform(-10, 10)

                cmds.setAttr(f"{blade}.translate", x, y, z)
                cmds.setAttr(f"{blade}.rotateY", random.uniform(0, 360) + ry_offset)
                cmds.setAttr(f"{blade}.rotateX", rx_offset)

                s = random.uniform(scale_min, scale_max)
                z_scale = random.uniform(0.8, 1.2)
                cmds.setAttr(f"{blade}.scaleX", s * z_scale)
                cmds.setAttr(f"{blade}.scaleY", s)
                cmds.setAttr(f"{blade}.scaleZ", s)

                cmds.parent(blade, clump_group)

        cmds.select(scatter_group)
        cmds.confirmDialog(title="Grass Scatter", message=f"{count} blades scattered with variation!", button=["OK"])

    def apply_wind(self):
        if not cmds.objExists("Grass_Scatter_Group"):
            cmds.warning("Scatter grass first!")
            return

        wind_speed = self.wind_speed_slider.value() / 10.0
        turbulence = self.turbulence_slider.value() / 10.0

        clumps = cmds.listRelatives("Grass_Scatter_Group", children=True, type="transform")
        if not clumps:
            cmds.warning("No clumps found!")
            return

        for clump in clumps:
            blades = cmds.listRelatives(clump, children=True, type="transform")
            for blade in blades:
                expr_name = f"{blade}_wind_expr"
                if cmds.objExists(expr_name):
                    cmds.delete(expr_name)
                phase = random.uniform(0, math.pi * 2)
                amplitude = random.uniform(2, 6)
                expr = f"""
float $t = frame;
{blade}.rotateZ = {amplitude}*sin($t*{wind_speed} + {phase});
{blade}.rotateX = {amplitude/2}*sin($t*{wind_speed*0.8} + {phase*0.5});
{blade}.rotateY = 1*sin($t*{wind_speed*0.5} + {phase*1.3});
"""
                cmds.expression(name=expr_name, string=expr, object=blade, alwaysEvaluate=True, unitConversion="all")

        cmds.confirmDialog(title="Wind Applied", message=f"Wind animation applied to all blades!", button=["OK"])


try:
    app.close()
except:
    pass

app = GrassClumpWindToolVaried()
app.show()

###อยากกินพิซซ่ากับโค้ก