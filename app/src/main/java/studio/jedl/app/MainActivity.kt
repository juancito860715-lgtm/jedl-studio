package studio.jedl.app

import android.app.Activity
import android.app.AlertDialog
import android.graphics.Canvas
import android.graphics.Color
import android.graphics.Matrix
import android.os.Bundle
import android.view.Gravity
import android.view.View
import android.widget.*
import kotlinx.coroutines.*
import studio.jedl.app.avatar.*
import studio.jedl.app.content.*
import studio.jedl.app.animation.PoseInterpolator
import kotlin.math.min

class MainActivity : Activity() {
    private val scope = CoroutineScope(SupervisorJob() + Dispatchers.Main.immediate)
    private lateinit var store: ProjectStore
    private lateinit var library: PieceLibrary
    private lateinit var contentLibrary: ContentLibrary
    private var selectedStyle: String = StylePackContract.DEFAULT_STYLE
    private var styleChangeInProgress = false
    private var project: StudioProject? = null
    private lateinit var content: LinearLayout
    private var preview: Preview? = null
    private var frame = 0
    private var playbackFrame = 0f
    private var playbackJob: Job? = null
    private var isPlaying = false
    private var playbackFrameLabel: TextView? = null
    private enum class Tab { SCENE, CHARACTER, LAYERS, ANIMATION, STYLE, LIBRARY }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        store = ProjectStore(this)
        showLoading("Preparando JEDL Studio…")
        scope.launch {
            try {
                val loaded = withContext(Dispatchers.IO) { PieceLibrary.load(applicationContext, selectedStyle) to ContentLibrary.load(applicationContext) }
                library = loaded.first
                contentLibrary = loaded.second
                home()
            } catch (e: Exception) { showLoading("Error al cargar recursos: ${e.message}") }
        }
    }

    private fun showLoading(message: String) {
        setContentView(TextView(this).apply {
            text = message; gravity = Gravity.CENTER; textSize = 18f; setPadding(24,24,24,24)
        })
    }

    private fun button(label: String, action: () -> Unit) = Button(this).apply {
        text = label; isAllCaps = false; setOnClickListener { action() }
    }
    private fun heading(label: String) = TextView(this).apply {
        text = label; textSize = 18f; setTextColor(Color.rgb(25,45,70)); setPadding(0,14,0,8)
    }
    private fun toast(s: String) = Toast.makeText(this,s,Toast.LENGTH_SHORT).show()

    private fun slotLabel(slot: CharacterLayerSlot): String = when (slot) {
        CharacterLayerSlot.HEAD -> "Cabeza"
        CharacterLayerSlot.EYES -> "Ojos"
        CharacterLayerSlot.EYEBROWS -> "Cejas"
        CharacterLayerSlot.MOUTH -> "Boca"
        CharacterLayerSlot.FACIAL_HAIR -> "Detalles del rostro"
        CharacterLayerSlot.HAIR_BACK -> "Cabello (parte trasera)"
        CharacterLayerSlot.HAIR_FRONT -> "Cabello (parte delantera)"
        CharacterLayerSlot.HAT_BACK -> "Gorra (parte trasera)"
        CharacterLayerSlot.HAT_FRONT -> "Gorra (parte delantera)"
        CharacterLayerSlot.TORSO -> "Torso"
        CharacterLayerSlot.SHIRT -> "Camiseta"
        CharacterLayerSlot.PANTS -> "Pantalón"
        CharacterLayerSlot.UPPER_ARM_L -> "Brazo superior izquierdo"
        CharacterLayerSlot.UPPER_ARM_R -> "Brazo superior derecho"
        CharacterLayerSlot.SLEEVE_L -> "Manga izquierda"
        CharacterLayerSlot.SLEEVE_R -> "Manga derecha"
        CharacterLayerSlot.FOREARM_L -> "Antebrazo izquierdo"
        CharacterLayerSlot.FOREARM_R -> "Antebrazo derecho"
        CharacterLayerSlot.HAND_L -> "Mano izquierda"
        CharacterLayerSlot.HAND_R -> "Mano derecha"
        CharacterLayerSlot.THIGH_L -> "Muslo izquierdo"
        CharacterLayerSlot.THIGH_R -> "Muslo derecho"
        CharacterLayerSlot.SHIN_L -> "Pantorrilla izquierda"
        CharacterLayerSlot.SHIN_R -> "Pantorrilla derecha"
        CharacterLayerSlot.SHOE_L -> "Calzado izquierdo"
        CharacterLayerSlot.SHOE_R -> "Calzado derecho"
    }

    private fun partLabel(id: String): String {
        val labels = mapOf(
            "head_skin" to "Piel de la cabeza",
            "face_eyes_dots" to "Ojos sencillos",
            "face_eyes_happy" to "Ojos alegres",
            "face_eyes_wide" to "Ojos sorprendidos",
            "face_mouth_smile" to "Sonrisa",
            "face_mouth_open" to "Boca abierta",
            "face_mouth_neutral" to "Boca neutra",
            "face_mouth_shout" to "Boca expresiva",
            "face_brows_normal" to "Cejas normales",
            "face_brows_raised" to "Cejas levantadas",
            "face_brows_angry" to "Cejas fruncidas",
            "face_blush" to "Rubor",
            "hair_short_back" to "Cabello corto, parte trasera",
            "hair_short_front" to "Cabello corto, parte delantera",
            "hair_spiky_back" to "Cabello puntiagudo, parte trasera",
            "hair_spiky_front" to "Cabello puntiagudo, parte delantera",
            "hair_curly_back" to "Cabello rizado, parte trasera",
            "hair_curly_front" to "Cabello rizado, parte delantera",
            "hat_cap_crown" to "Corona de la gorra",
            "hat_cap_panel" to "Panel de la gorra",
            "hat_cap_brim" to "Visera de la gorra",
            "torso_skin" to "Piel del torso",
            "shirt_tee_torso" to "Camiseta",
            "pants_jeans_waist" to "Pantalón vaquero",
            "armu_skin_l" to "Brazo superior izquierdo",
            "armu_skin_r" to "Brazo superior derecho",
            "shirt_tee_sleeve_l" to "Manga izquierda",
            "shirt_tee_sleeve_r" to "Manga derecha",
            "forearm_skin_open_l" to "Antebrazo izquierdo",
            "forearm_skin_open_r" to "Antebrazo derecho",
            "hand_open_l" to "Mano izquierda abierta",
            "hand_open_r" to "Mano derecha abierta",
            "hand_fist_l" to "Mano izquierda cerrada",
            "hand_fist_r" to "Mano derecha cerrada",
            "thigh_jeans_l" to "Muslo izquierdo",
            "thigh_jeans_r" to "Muslo derecho",
            "shin_jeans_l" to "Pantorrilla izquierda",
            "shin_jeans_r" to "Pantorrilla derecha",
            "shoe_sneaker_upper_l" to "Parte superior del calzado izquierdo",
            "shoe_sneaker_upper_r" to "Parte superior del calzado derecho",
            "shoe_sneaker_sole_l" to "Suela del calzado izquierdo",
            "shoe_sneaker_sole_r" to "Suela del calzado derecho"
        )
        // No exponer nunca IDs internos: todos los IDs generados están cubiertos por el diccionario.
        return labels[id] ?: "Pieza del personaje"
    }

    private fun home() {
        project = null
        val root = LinearLayout(this).apply {
            orientation = LinearLayout.VERTICAL; setPadding(24,30,24,24)
            setBackgroundColor(Color.rgb(241,245,250))
        }
        root.addView(heading("JEDL STUDIO"))
        root.addView(TextView(this).apply { text = "Estudio de producción de bolsillo"; textSize=15f })
        root.addView(button("＋ Crear proyecto") {
            val name = EditText(this).apply { hint = "Nombre del proyecto" }
            AlertDialog.Builder(this).setTitle("Nuevo proyecto").setView(name)
                .setNegativeButton("Cancelar",null).setPositiveButton("Crear") { _,_ ->
                    runCatching { store.create(name.text.toString()) }
                        .onSuccess { openProject(it) }.onFailure { toast(it.message ?: "Error") }
                }.show()
        })
        root.addView(heading("Abrir proyecto"))
        val saved = store.list()
        if (saved.isEmpty()) root.addView(TextView(this).apply {
            text = "No hay proyectos guardados todavía."; setPadding(0,12,0,12)
        })
        saved.forEach { p -> root.addView(button("Abrir: ${p.name}") { openProject(p) }) }
        setContentView(ScrollView(this).apply { addView(root) })
    }

    private fun openProject(p: StudioProject) { project=p; frame=0; studio(Tab.SCENE) }
    private fun save() {
        project?.let { runCatching { store.save(it) }.onSuccess { toast("Proyecto guardado") }
            .onFailure { toast("Error al guardar: ${it.message}") } }
    }

    private fun studio(tab: Tab) {
        val p = project ?: return home()
        val root = LinearLayout(this).apply { orientation=LinearLayout.VERTICAL; setBackgroundColor(Color.rgb(238,242,248)) }
        val top = LinearLayout(this).apply { gravity=Gravity.CENTER_VERTICAL; setPadding(8,4,8,4) }
        top.addView(TextView(this).apply { text=p.name; textSize=18f; setTextColor(Color.BLACK) },
            LinearLayout.LayoutParams(0,-2,1f))
        top.addView(button("Guardar") { save() })
        top.addView(button("Inicio") { save(); home() })
        root.addView(top)
        preview = Preview(this, library, contentLibrary, p)
        root.addView(preview, LinearLayout.LayoutParams(-1,0,1f))
        val tabs=LinearLayout(this).apply { orientation=LinearLayout.HORIZONTAL }
        listOf(Tab.SCENE to "Escena",Tab.CHARACTER to "Personaje",Tab.LAYERS to "Capas",Tab.ANIMATION to "Animación",Tab.STYLE to "Estilo",Tab.LIBRARY to "Biblioteca")
            .forEach { (t,label) -> tabs.addView(button(label) { studio(t) },LinearLayout.LayoutParams(0,-2,1f)) }
        root.addView(tabs)
        content=LinearLayout(this).apply { orientation=LinearLayout.VERTICAL; setPadding(12,8,12,20) }
        root.addView(ScrollView(this).apply { addView(content) },LinearLayout.LayoutParams(-1,0,1f))
        setContentView(root)
        when(tab) {
            Tab.SCENE -> {
                content.addView(heading("Escenario de trabajo"))
                content.addView(TextView(this).apply { text="Vista del personaje. Usa las pestañas para editar piezas, capas y poses." })
                content.addView(button("Guardar proyecto") { save() })
            }
            Tab.CHARACTER -> characterPanel()
            Tab.LAYERS -> layersPanel()
            Tab.ANIMATION -> animationPanel()
            Tab.STYLE -> stylePanel()
            Tab.LIBRARY -> libraryPanel()
        }
    }



    private fun libraryPanel() {
        content.addView(heading("Biblioteca de contenido"))
        content.addView(TextView(this).apply {
            text = "Recursos CC0. Toca un elemento para incorporarlo a la escena."
        })
        var activeKind = ContentKind.OBJECT
        val bankSpinner = Spinner(this)
        val list = ListView(this)
        val count = TextView(this)
        val placed = LinearLayout(this).apply { orientation = LinearLayout.VERTICAL }
        var refreshPlaced: () -> Unit = {}
        fun refreshItems(bank: ContentBank) {
            val assets = bank.assets
            count.text = assets.size.toString() + " recursos · " + bank.license + " · " + bank.title
            list.adapter = object : android.widget.BaseAdapter() {
                override fun getCount() = assets.size
                override fun getItem(position: Int) = assets[position]
                override fun getItemId(position: Int) = position.toLong()
                override fun getView(position: Int, convertView: View?, parent: android.view.ViewGroup): View {
                    val item = assets[position]
                    val row = LinearLayout(this@MainActivity).apply {
                        orientation = LinearLayout.HORIZONTAL
                        gravity = Gravity.CENTER_VERTICAL
                        setPadding(8, 6, 8, 6)
                    }
                    val thumb = ImageView(this@MainActivity).apply {
                        tag = item.id
                        scaleType = ImageView.ScaleType.FIT_CENTER
                    }
                    row.addView(thumb, LinearLayout.LayoutParams(56, 56))
                    scope.launch {
                        val bitmap = withContext(Dispatchers.IO) { contentLibrary.thumbnail(item) }
                        if (thumb.tag == item.id) thumb.setImageBitmap(bitmap)
                    }
                    row.addView(TextView(this@MainActivity).apply {
                        text = item.category + " · " + item.title + " (" + item.width + "×" + item.height + ")"
                        textSize = 14f
                        setPadding(10, 0, 0, 0)
                    }, LinearLayout.LayoutParams(0, -2, 1f))
                    return row
                }
            }
            list.setOnItemClickListener { _, _, index, _ ->
                val asset = assets[index]
                val now = project ?: return@setOnItemClickListener
                val baseSize = if (asset.kind == ContentKind.CHARACTER_PART) 0.10f else 0.14f
                val objectItem = SceneObjectInstance(
                    assetId = asset.id,
                    x = ((now.sceneObjects.size % 5) - 2) * 0.13f,
                    y = 0.42f + ((now.sceneObjects.size / 5) % 4) * 0.13f,
                    width = baseSize,
                    height = ((asset.height.toFloat() / asset.width.coerceAtLeast(1)) * baseSize).coerceIn(0.01f, 1.5f)
                )
                project = now.copy(sceneObjects = now.sceneObjects + objectItem)
                preview?.update(project!!)
                toast("Recurso añadido a la escena")
                refreshPlaced()
            }
        }
        fun refreshBanks() {
            val banks = contentLibrary.banks.filter { it.kind == activeKind }
            bankSpinner.adapter = ArrayAdapter(this, android.R.layout.simple_spinner_dropdown_item, banks.map { it.title })
            bankSpinner.onItemSelectedListener = object : android.widget.AdapterView.OnItemSelectedListener {
                override fun onNothingSelected(parent: android.widget.AdapterView<*>?) {}
                override fun onItemSelected(parent: android.widget.AdapterView<*>?, view: View?, position: Int, id: Long) {
                    banks.getOrNull(position)?.let { refreshItems(it) }
                }
            }
            banks.firstOrNull()?.let { refreshItems(it) }
        }
        refreshPlaced = {
            placed.removeAllViews()
            val now = project
            now?.sceneObjects?.forEachIndexed { index, item ->
                val asset = contentLibrary.find(item.assetId)
                val row = LinearLayout(this).apply { gravity = Gravity.CENTER_VERTICAL }
                row.addView(TextView(this).apply {
                    text = asset?.title ?: item.assetId
                    textSize = 13f
                }, LinearLayout.LayoutParams(0, -2, 1f))
                fun adjust(change: (SceneObjectInstance) -> SceneObjectInstance) {
                    val current = project ?: return
                    project = current.copy(sceneObjects = current.sceneObjects.mapIndexed { i, value ->
                        if (i == index) change(value) else value
                    })
                    preview?.update(project!!)
                }
                row.addView(button("←") { adjust { it.copy(x = (it.x - 0.04f).coerceIn(-2f, 2f)) } })
                row.addView(button("→") { adjust { it.copy(x = (it.x + 0.04f).coerceIn(-2f, 2f)) } })
                row.addView(button("↑") { adjust { it.copy(y = (it.y - 0.04f).coerceIn(-2f, 2f)) } })
                row.addView(button("↓") { adjust { it.copy(y = (it.y + 0.04f).coerceIn(-2f, 2f)) } })
                row.addView(button("+") { adjust { it.copy(width = (it.width * 1.15f).coerceAtMost(1.5f), height = (it.height * 1.15f).coerceAtMost(1.5f)) } })
                row.addView(button("−") { adjust { it.copy(width = (it.width / 1.15f).coerceAtLeast(0.01f), height = (it.height / 1.15f).coerceAtLeast(0.01f)) } })
                row.addView(button("↶") { adjust { it.copy(rotation = (it.rotation - 15f).coerceAtLeast(-360f)) } })
                row.addView(button("↷") { adjust { it.copy(rotation = (it.rotation + 15f).coerceAtMost(360f)) } })
                row.addView(button("×") {
                    val current = project ?: return@button
                    project = current.copy(sceneObjects = current.sceneObjects.filterIndexed { i, _ -> i != index })
                    preview?.update(project!!)
                    refreshPlaced()
                })
                placed.addView(row)
            }
        }
        content.addView(button("Objetos y escenarios") { activeKind = ContentKind.OBJECT; refreshBanks() })
        content.addView(button("Piezas de personajes") { activeKind = ContentKind.CHARACTER_PART; refreshBanks() })
        content.addView(heading("Paquete"))
        content.addView(bankSpinner)
        content.addView(count)
        content.addView(list, LinearLayout.LayoutParams(-1, 520))
        content.addView(heading("Elementos colocados"))
        content.addView(placed)
        refreshBanks()
        refreshPlaced()
    }

    private fun stylePanel() {
        content.addView(heading("Estilo visual"))
        content.addView(TextView(this).apply {
            text = "Cambia la apariencia sin modificar las poses, las capas ni la animación."
        })
        val styles = PieceLibrary.availableStyles(this)
        if (styles.isEmpty()) {
            content.addView(TextView(this).apply { text = "No hay paquetes de estilos disponibles." })
            return
        }
        styles.forEach { style ->
            val label = when (style) {
                "default" -> "Color original"
                "boceto" -> "Boceto en blanco y negro"
                else -> "Estilo " + style.replace('_', ' ')
            }
            content.addView(button((if (style == selectedStyle) "✓ " else "") + label) {
                if (style != selectedStyle) applyStyle(style)
            })
        }
        content.addView(TextView(this).apply {
            text = "Los paquetes pueden aportar piezas diferentes, pero deben conservar el rig humanoide, sus huesos y las ranuras del editor."
            setPadding(0, 10, 0, 0)
        })
    }

    private fun applyStyle(style: String) {
        if (styleChangeInProgress) return
        styleChangeInProgress = true
        toast("Cargando estilo…")
        scope.launch {
            try {
                val next = withContext(Dispatchers.IO) {
                    PieceLibrary.load(applicationContext, style).also { candidate ->
                        try {
                            candidate.requireCompatibleWith(library)
                        } catch (failure: Exception) {
                            candidate.close()
                            throw failure
                        }
                    }
                }
                val previous = library
                val currentProject = project
                if (currentProject != null) {
                    project = currentProject.copy(
                        selectedParts = next.compatibleSelection(currentProject.selectedParts)
                    )
                }
                library = next
                selectedStyle = next.selectedStyle
                preview?.replaceLibrary(next)
                project?.let { preview?.update(it) }
                previous.close()
                studio(Tab.STYLE)
                toast("Estilo aplicado")
            } catch (failure: Exception) {
                toast("No se pudo aplicar el estilo: ${failure.message}")
            } finally {
                styleChangeInProgress = false
            }
        }
    }

    private fun characterPanel() {
        val p=project ?: return
        content.addView(heading("Personajes preconfigurados"))
        content.addView(TextView(this).apply {
            text = "Selecciona una apariencia completa y después personaliza sus piezas."
        })
        contentLibrary.presets.forEach { preset ->
            content.addView(button(preset.title) {
                val current = project ?: p
                project = current.copy(selectedParts = preset.selectedParts)
                preview?.update(project!!)
                toast("Apariencia aplicada: " + preset.title)
            })
        }
        content.addView(heading("Personalizar piezas del personaje"))
        CharacterLayerSlot.values().forEach { slot ->
            val choices=library.parts.filter { it.slot==slot }
            if (choices.size<2) return@forEach
            val current=p.selectedParts[slot.name] ?: library.defaults[slot]
            content.addView(button("${slotLabel(slot)}: ${current?.let(::partLabel) ?: "predeterminado"}") {
                val labels=choices.map { it.id }.toTypedArray()
                AlertDialog.Builder(this).setTitle("Elegir ${slotLabel(slot)}")
                    .setSingleChoiceItems(choices.map { partLabel(it.id) }.toTypedArray(),choices.indexOfFirst { it.id==current }.coerceAtLeast(0)) { dialog,which ->
                        project=(project ?: p).copy(selectedParts=(project ?: p).selectedParts+(slot.name to choices[which].id))
                        preview?.update(project!!); dialog.dismiss(); studio(Tab.CHARACTER)
                    }.setNegativeButton("Cancelar",null).show()
            })
        }
        content.addView(heading("Colores del personaje"))
        val colorLabels = linkedMapOf(
            "skin" to "Piel", "hair" to "Cabello", "shirt" to "Camiseta",
            "pants" to "Pantalón", "shoe" to "Zapatos", "sole" to "Suela",
            "hat_crown" to "Corona de gorra", "hat_panel" to "Panel de gorra",
            "hat_brim" to "Visera"
        )
        colorLabels.forEach { (channel, label) ->
            val color = p.colors[channel] ?: AvatarColorPalette.DEFAULTS.getValue(channel)
            content.addView(button(label + " · " + String.format("#%06X", color and 0xFFFFFF)) {
                showColorPicker(channel, label, color)
            })
        }
        content.addView(button("Guardar cambios") { save() })
    }

    private fun showColorPicker(channel: String, label: String, initialColor: Int) {
        var red = (initialColor shr 16) and 0xFF
        var green = (initialColor shr 8) and 0xFF
        var blue = initialColor and 0xFF
        var selectedColor = Color.rgb(red, green, blue)
        val previewColor = TextView(this).apply {
            text = String.format("#%06X", selectedColor and 0xFFFFFF)
            textSize = 18f
            gravity = Gravity.CENTER
            setPadding(12, 18, 12, 18)
            setBackgroundColor(selectedColor)
        }
        val panel = LinearLayout(this).apply {
            orientation = LinearLayout.VERTICAL
            setPadding(24, 12, 24, 8)
        }
        panel.addView(previewColor, LinearLayout.LayoutParams(-1, 72))
        fun addChannelSlider(name: String, initial: Int, changed: (Int) -> Unit) {
            panel.addView(TextView(this).apply { text = name })
            val slider = SeekBar(this).apply {
                max = 255
                progress = initial
            }
            slider.setOnSeekBarChangeListener(object : SeekBar.OnSeekBarChangeListener {
                override fun onProgressChanged(seekBar: SeekBar?, value: Int, fromUser: Boolean) {
                    changed(value)
                    selectedColor = Color.rgb(red, green, blue)
                    previewColor.text = String.format("#%06X", selectedColor and 0xFFFFFF)
                    previewColor.setBackgroundColor(selectedColor)
                }
                override fun onStartTrackingTouch(seekBar: SeekBar?) {}
                override fun onStopTrackingTouch(seekBar: SeekBar?) {}
            })
            panel.addView(slider)
        }
        addChannelSlider("Rojo", red) { red = it }
        addChannelSlider("Verde", green) { green = it }
        addChannelSlider("Azul", blue) { blue = it }
        AlertDialog.Builder(this)
            .setTitle("Color: " + label)
            .setView(panel)
            .setNegativeButton("Cancelar", null)
            .setNeutralButton("Restablecer") { _, _ ->
                val current = project ?: return@setNeutralButton
                project = current.copy(colors = current.colors + (channel to AvatarColorPalette.DEFAULTS.getValue(channel)))
                preview?.update(project!!)
                studio(Tab.CHARACTER)
            }
            .setPositiveButton("Aplicar") { _, _ ->
                val current = project ?: return@setPositiveButton
                project = current.copy(colors = current.colors + (channel to selectedColor))
                preview?.update(project!!)
                studio(Tab.CHARACTER)
            }
            .show()
    }

    private fun layersPanel() {
        val p=project ?: return
        val manifestOrder=library.parts.groupBy { it.slot.name }.entries
            .sortedBy { e -> e.value.minOf { it.zIndex } }.map { it.key }
        val order=((if(p.layerOrder.isEmpty()) manifestOrder else p.layerOrder+manifestOrder)).distinct().toMutableList()
        content.addView(heading("Mostrar, ocultar y ordenar capas"))
        order.toList().forEach { slot ->
            val row=LinearLayout(this).apply { gravity=Gravity.CENTER_VERTICAL }
            row.addView(CheckBox(this).apply {
                text=slotLabel(CharacterLayerSlot.valueOf(slot)); isChecked=slot !in (project ?: p).hiddenSlots
                setOnCheckedChangeListener { _,checked ->
                    val now=project ?: p
                    project=now.copy(hiddenSlots=if(checked) now.hiddenSlots-slot else now.hiddenSlots+slot,layerOrder=order)
                    preview?.update(project!!)
                }
            },LinearLayout.LayoutParams(0,-2,1f))
            row.addView(button("↑") {
                val i=order.indexOf(slot); if(i>0) { val v=order.removeAt(i); order.add(i-1,v); project=(project?:p).copy(layerOrder=order); preview?.update(project!!); layersPanelRefresh() }
            })
            row.addView(button("↓") {
                val i=order.indexOf(slot); if(i<order.lastIndex) { val v=order.removeAt(i); order.add(i+1,v); project=(project?:p).copy(layerOrder=order); preview?.update(project!!); layersPanelRefresh() }
            })
            content.addView(row)
        }
        content.addView(button("Guardar capas") { save() })
    }
    private fun layersPanelRefresh() { studio(Tab.LAYERS) }

    private fun togglePlayback() {
        if (isPlaying) {
            stopPlayback()
            return
        }
        val current = project ?: return
        if (current.keyframes.size < 2) {
            toast("Guarda al menos dos fotogramas clave para reproducir")
            return
        }
        isPlaying = true
        playbackFrame = frame.toFloat()
        studio(Tab.ANIMATION)
        playbackJob = scope.launch {
            while (isActive) {
                val active = project ?: break
                val pose = PoseInterpolator.interpolate(
                    active.keyframes, playbackFrame, active.durationFrames, loop = true
                )
                preview?.update(active.copy(pose = pose))
                frame = playbackFrame.toInt().coerceIn(0, active.durationFrames - 1)
                playbackFrameLabel?.text = "Reproduciendo · Fotograma: " + frame + " / " + (active.durationFrames - 1)
                playbackFrame = (playbackFrame + 1f) % active.durationFrames
                delay(33L)
            }
        }
    }

    private fun stopPlayback() {
        playbackJob?.cancel()
        playbackJob = null
        isPlaying = false
        project?.let { preview?.update(it) }
        studio(Tab.ANIMATION)
    }

    private fun animationPanel() {
        val p=project ?: return
        frame=frame.coerceIn(0,p.durationFrames-1)
        content.addView(heading("Editor de poses y fotogramas"))
        val frameLabel=TextView(this).apply { text="Fotograma: $frame / ${p.durationFrames-1}" }
        playbackFrameLabel = frameLabel
        content.addView(button(if (isPlaying) "Stop" else "Play") { togglePlayback() })
        content.addView(frameLabel)
        content.addView(SeekBar(this).apply {
            max=p.durationFrames-1; progress=frame
            setOnSeekBarChangeListener(object:SeekBar.OnSeekBarChangeListener {
                override fun onProgressChanged(s:SeekBar?,v:Int,user:Boolean) { if(user){frame=v;frameLabel.text="Fotograma: $v / ${p.durationFrames-1}"} }
                override fun onStartTrackingTouch(s:SeekBar?) {}
                override fun onStopTrackingTouch(s:SeekBar?) {}
            })
        })
        listOf("torso","head","armUL","foreArmL","armUR","foreArmR","thighL","shinL","thighR","shinR").forEach { bone ->
            val boneName = mapOf("torso" to "Torso", "head" to "Cabeza", "armUL" to "Brazo superior izquierdo",
                "foreArmL" to "Antebrazo izquierdo", "armUR" to "Brazo superior derecho",
                "foreArmR" to "Antebrazo derecho", "thighL" to "Muslo izquierdo",
                "shinL" to "Pantorrilla izquierda", "thighR" to "Muslo derecho",
                "shinR" to "Pantorrilla derecha")[bone] ?: bone
            content.addView(TextView(this).apply { text="Rotación: $boneName" })
            content.addView(SeekBar(this).apply {
                max=360; progress=((p.pose[bone]?:0f)+180).toInt().coerceIn(0,360)
                setOnSeekBarChangeListener(object:SeekBar.OnSeekBarChangeListener {
                    override fun onProgressChanged(s:SeekBar?,v:Int,user:Boolean) {
                        if(user){ project=(project?:p).copy(pose=(project?:p).pose+(bone to (v-180).toFloat())); preview?.update(project!!) }
                    }
                    override fun onStartTrackingTouch(s:SeekBar?) {}
                    override fun onStopTrackingTouch(s:SeekBar?) {}
                })
            })
        }
        content.addView(button("＋ Guardar fotograma clave") {
            val now=project ?: p
            project=now.copy(keyframes=(now.keyframes.filterNot{it.frame==frame}+StudioKeyframe(frame,now.pose)).sortedBy{it.frame})
            studio(Tab.ANIMATION); toast("Fotograma guardado")
        })
        content.addView(button("Eliminar fotograma clave actual") {
            project=(project?:p).copy(keyframes=(project?:p).keyframes.filterNot{it.frame==frame}); studio(Tab.ANIMATION)
        })
        (project ?: p).keyframes.sortedBy{it.frame}.forEach { key ->
            content.addView(button("Cargar fotograma ${key.frame}") {
                frame=key.frame; project=(project?:p).copy(pose=key.pose); preview?.update(project!!); studio(Tab.ANIMATION)
            })
        }
        content.addView(button("Guardar animación") { save() })
    }

    override fun onDestroy() {
        playbackJob?.cancel()
        scope.cancel()
        if (::library.isInitialized) library.close()
        if (::contentLibrary.isInitialized) contentLibrary.close()
        super.onDestroy()
    }
}

private class Preview(context:android.content.Context,private var library:PieceLibrary,private val contentLibrary:ContentLibrary,initial:StudioProject):View(context) {
    private var p=initial
    private val renderer=AvatarRenderer()
    fun update(value:StudioProject){p=value;invalidate()}
    fun replaceLibrary(value: PieceLibrary) { library = value; invalidate() }
    override fun onDraw(c:Canvas){
        super.onDraw(c); c.drawColor(Color.WHITE); if(width==0||height==0)return
        val scale=min(width/0.42f,height/1.52f)*0.97f
        val matrices=PoseHierarchy.solve(p.pose).mapValues { (_, transform) -> transform.toAndroidMatrix() }
        val save=c.save()
        try{
            c.translate(width/2f,height*0.52f);c.scale(scale,scale)
            val selection=p.selectedParts.mapNotNull{(key,id)->runCatching{CharacterLayerSlot.valueOf(key)}.getOrNull()?.let{it to id}}.toMap()
            p.sceneObjects.forEach { placed ->
                val asset = contentLibrary.find(placed.assetId) ?: return@forEach
                val bitmap = contentLibrary.bitmap(asset)
                val itemSave = c.save()
                try {
                    c.rotate(placed.rotation, placed.x, placed.y)
                    c.drawBitmap(bitmap, null, android.graphics.RectF(
                        placed.x - placed.width / 2f, placed.y - placed.height / 2f,
                        placed.x + placed.width / 2f, placed.y + placed.height / 2f
                    ), android.graphics.Paint(android.graphics.Paint.ANTI_ALIAS_FLAG or android.graphics.Paint.FILTER_BITMAP_FLAG))
                } finally { c.restoreToCount(itemSave) }
            }
            renderer.draw(c,library,matrices,selection,colors=p.colors,visibleSlots=StudioProject.SLOT_NAMES-p.hiddenSlots,layerOrder=p.layerOrder)
        }finally{c.restoreToCount(save)}
    }
}
