package com.example.geometrysolver

import android.graphics.Bitmap
import android.graphics.BitmapFactory
import android.net.Uri
import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.compose.setContent
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.foundation.Image
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.asImageBitmap
import androidx.compose.ui.layout.ContentScale
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.chaquo.python.Python
import com.chaquo.python.android.AndroidPlatform
import com.google.mlkit.vision.common.InputImage
import com.google.mlkit.vision.text.TextRecognition
import com.google.mlkit.vision.text.chinese.ChineseTextRecognizerOptions
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext
import org.json.JSONObject
import kotlin.coroutines.resume
import kotlin.coroutines.suspendCoroutine

data class SolveResult(
    val problemType: String,
    val conditions: List<String>,
    val theorems: List<String>,
    val steps: List<String>,
    val finalAnswer: String
)

class MainActivity : ComponentActivity() {

    private var onnxDetector: GeometryOnnxDetector? = null

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)

        // 1. 初始化 Chaquopy 离线 Python 运行环境
        try {
            if (!Python.isStarted()) {
                Python.start(AndroidPlatform(this))
            }
        } catch (e: Throwable) {
            e.printStackTrace()
        }

        // 2. 初始化 ONNX Runtime 几何特征提取引擎
        try {
            onnxDetector = GeometryOnnxDetector(this)
        } catch (e: Throwable) {
            e.printStackTrace()
        }

        setContent {
            MaterialTheme {
                Surface(
                    modifier = Modifier.fillMaxSize(),
                    color = MaterialTheme.colorScheme.background
                ) {
                    val statusText = if (onnxDetector?.isInitialized == true) {
                        "✅ ONNX 模型加载就绪 (IR v9 / MobileNetV2)"
                    } else {
                        "⚠️ 模型状态: ${onnxDetector?.errorMessage ?: "未完成加载"}"
                    }
                    GeometrySolverScreen(
                        modelStatus = statusText,
                        onnxDetector = onnxDetector
                    )
                }
            }
        }
    }

    override fun onDestroy() {
        super.onDestroy()
        onnxDetector?.close()
    }
}

// 离线中英文 OCR 识别
suspend fun recognizeTextFromBitmap(bitmap: Bitmap): String = suspendCoroutine { continuation ->
    try {
        val recognizer = TextRecognition.getClient(ChineseTextRecognizerOptions.Builder().build())
        val inputImage = InputImage.fromBitmap(bitmap, 0)
        recognizer.process(inputImage)
            .addOnSuccessListener { visionText ->
                continuation.resume(visionText.text)
            }
            .addOnFailureListener { e ->
                continuation.resume("OCR 识别提示: ${e.localizedMessage ?: "未检测到清晰文字"}")
            }
    } catch (t: Throwable) {
        continuation.resume("OCR 引擎提示: ${t.localizedMessage}")
    }
}

// 本地 SymPy 神经符号几何定理推导
suspend fun solveFromText(ocrText: String): SolveResult = withContext(Dispatchers.Default) {
    try {
        val py = Python.getInstance()
        val solverModule = py.getModule("geometry_solver")
        val jsonStr = solverModule.callAttr("solve_geometry", ocrText).toString()
        val json = JSONObject(jsonStr)

        val problemType = json.optString("problem_type", "几何题形式化推导")
        val finalAnswer = json.optString("final_answer", "")

        val stepsList = mutableListOf<String>()
        val stepsArray = json.optJSONArray("steps")
        if (stepsArray != null) {
            for (i in 0 until stepsArray.length()) {
                stepsList.add(stepsArray.getString(i))
            }
        }

        val conditionsList = mutableListOf<String>()
        val condArray = json.optJSONArray("identified_conditions")
        if (condArray != null) {
            for (i in 0 until condArray.length()) {
                conditionsList.add(condArray.getString(i))
            }
        }

        val theoremsList = mutableListOf<String>()
        val theoArray = json.optJSONArray("theorems_used")
        if (theoArray != null) {
            for (i in 0 until theoArray.length()) {
                theoremsList.add(theoArray.getString(i))
            }
        }

        SolveResult(
            problemType = problemType,
            conditions = conditionsList,
            theorems = theoremsList,
            steps = stepsList,
            finalAnswer = finalAnswer
        )
    } catch (e: Throwable) {
        SolveResult(
            problemType = "推导异常",
            conditions = emptyList(),
            theorems = emptyList(),
            steps = listOf("错误详情: " + (e.localizedMessage ?: e.toString())),
            finalAnswer = "计算未完成"
        )
    }
}

@Composable
fun GeometrySolverScreen(
    modelStatus: String = "",
    onnxDetector: GeometryOnnxDetector? = null
) {
    val context = LocalContext.current
    val scope = rememberCoroutineScope()
    val scrollState = rememberScrollState()

    var imageBitmap by remember { mutableStateOf<Bitmap?>(null) }
    var recognizedText by remember { mutableStateOf("") }
    var detectedFeatureInfo by remember { mutableStateOf("") }
    var isProcessing by remember { mutableStateOf(false) }
    var statusStage by remember { mutableStateOf("") }
    var solveResult by remember { mutableStateOf<SolveResult?>(null) }

    // 处理新图片流程 (拍照或相册选图后触发)
    fun processImage(bitmap: Bitmap) {
        imageBitmap = bitmap
        isProcessing = true
        statusStage = "🔍 正在进行端侧特征提取与离线 OCR 识别..."

        scope.launch {
            // 1. ONNX 神经特征提取
            val featMap = withContext(Dispatchers.Default) {
                onnxDetector?.extractFeatures(bitmap) ?: emptyMap()
            }
            detectedFeatureInfo = if (featMap.containsKey("error")) {
                "特征提取: ${featMap["error"]}"
            } else {
                "✓ 已提取 P2~P7 几何特征金字塔 (${featMap.size} 组尺度)"
            }

            // 2. 离线 OCR 识别题目文字
            statusStage = "📝 正在识别图中几何已知量与文字..."
            val ocr = recognizeTextFromBitmap(bitmap)
            recognizedText = ocr

            // 3. 自动定理推导与几何求解
            statusStage = "⚡ 正在调用 SymPy 形式化几何定理库推导求解..."
            val result = solveFromText(ocr)
            solveResult = result

            isProcessing = false
            statusStage = ""
        }
    }

    // 1. 真实系统拍照
    val takePhotoLauncher = rememberLauncherForActivityResult(
        contract = ActivityResultContracts.TakePicturePreview()
    ) { bitmap: Bitmap? ->
        bitmap?.let { processImage(it) }
    }

    // 2. 系统相册选图
    val pickImageLauncher = rememberLauncherForActivityResult(
        contract = ActivityResultContracts.GetContent()
    ) { uri: Uri? ->
        uri?.let {
            val bitmap = try {
                context.contentResolver.openInputStream(it)?.use { stream ->
                    BitmapFactory.decodeStream(stream)
                }
            } catch (t: Throwable) {
                null
            }
            bitmap?.let { b -> processImage(b) }
        }
    }

    Column(
        modifier = Modifier
            .fillMaxSize()
            .verticalScroll(scrollState)
            .padding(16.dp),
        horizontalAlignment = Alignment.CenterHorizontally
    ) {
        Text(
            text = "📐 几何全要素智能识别与解题器",
            fontSize = 20.sp,
            fontWeight = FontWeight.Bold,
            modifier = Modifier.padding(vertical = 8.dp)
        )

        // 状态说明卡片
        Card(
            modifier = Modifier.fillMaxWidth(),
            shape = RoundedCornerShape(12.dp),
            colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surfaceVariant)
        ) {
            Column(modifier = Modifier.padding(12.dp)) {
                Text(text = "📱 运行模式: 纯端侧全离线 (无需联网)", fontWeight = FontWeight.SemiBold, fontSize = 14.sp)
                Text(text = "• 模型引擎: $modelStatus", fontSize = 12.sp, color = MaterialTheme.colorScheme.primary)
                Text(text = "• 求解引擎: Chaquopy + SymPy 几何形式化推导", fontSize = 12.sp, color = Color.Gray)
            }
        }

        Spacer(modifier = Modifier.height(14.dp))

        // 拍照与选图核心操作区
        Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.spacedBy(10.dp)
        ) {
            Button(
                onClick = { takePhotoLauncher.launch(null) },
                modifier = Modifier.weight(1f).height(48.dp),
                shape = RoundedCornerShape(8.dp)
            ) {
                Text(text = "📸 真实拍照", fontSize = 15.sp)
            }

            Button(
                onClick = { pickImageLauncher.launch("image/*") },
                modifier = Modifier.weight(1f).height(48.dp),
                colors = ButtonDefaults.buttonColors(containerColor = MaterialTheme.colorScheme.secondary),
                shape = RoundedCornerShape(8.dp)
            ) {
                Text(text = "🖼️ 相册选图", fontSize = 15.sp)
            }
        }

        // 显示已拍摄/选择的题目图片
        if (imageBitmap != null) {
            Spacer(modifier = Modifier.height(12.dp))
            Card(
                modifier = Modifier.fillMaxWidth(),
                shape = RoundedCornerShape(12.dp)
            ) {
                Column(modifier = Modifier.padding(8.dp)) {
                    Text(text = "📷 题目拍摄预览:", fontWeight = FontWeight.SemiBold, fontSize = 13.sp)
                    Spacer(modifier = Modifier.height(6.dp))
                    Image(
                        bitmap = imageBitmap!!.asImageBitmap(),
                        contentDescription = "题目图片",
                        modifier = Modifier
                            .fillMaxWidth()
                            .height(200.dp)
                            .clip(RoundedCornerShape(8.dp))
                            .background(Color.Black),
                        contentScale = ContentScale.Fit
                    )
                    if (detectedFeatureInfo.isNotEmpty()) {
                        Text(
                            text = detectedFeatureInfo,
                            fontSize = 11.sp,
                            color = Color(0xFF2E7D32),
                            modifier = Modifier.padding(top = 4.dp)
                        )
                    }
                }
            }
        }

        // 正在处理指示器
        if (isProcessing) {
            Spacer(modifier = Modifier.height(12.dp))
            Card(
                modifier = Modifier.fillMaxWidth(),
                shape = RoundedCornerShape(8.dp),
                colors = CardDefaults.cardColors(containerColor = Color(0xFFFFF3E0))
            ) {
                Row(
                    modifier = Modifier.padding(12.dp),
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    CircularProgressIndicator(modifier = Modifier.size(20.dp), strokeWidth = 2.dp)
                    Spacer(modifier = Modifier.width(12.dp))
                    Text(text = statusStage, fontSize = 13.sp, color = Color(0xFFE65100))
                }
            }
        }

        // 识别到的题目文本（支持用户直接修改或手动输入）
        Spacer(modifier = Modifier.height(12.dp))
        Card(
            modifier = Modifier.fillMaxWidth(),
            shape = RoundedCornerShape(12.dp)
        ) {
            Column(modifier = Modifier.padding(12.dp)) {
                Text(text = "📝 题目文本 (OCR 结果，可直接编辑修改):", fontWeight = FontWeight.SemiBold, fontSize = 13.sp)
                Spacer(modifier = Modifier.height(6.dp))
                OutlinedTextField(
                    value = recognizedText,
                    onValueChange = { recognizedText = it },
                    placeholder = { Text("在此输入或粘贴几何题目文字，例如：在Rt△ABC中，∠C=90°，AB=13，AC=5，求BC的长") },
                    modifier = Modifier
                        .fillMaxWidth()
                        .heightIn(min = 90.dp, max = 160.dp),
                    shape = RoundedCornerShape(8.dp)
                )

                Spacer(modifier = Modifier.height(10.dp))
                Button(
                    onClick = {
                        scope.launch {
                            isProcessing = true
                            statusStage = "⚡ 正在推导几何定理求解..."
                            solveResult = solveFromText(recognizedText)
                            isProcessing = false
                            statusStage = ""
                        }
                    },
                    modifier = Modifier.fillMaxWidth().height(44.dp),
                    shape = RoundedCornerShape(8.dp)
                ) {
                    Text(text = "⚡ 立即推导求解几何题", fontSize = 14.sp)
                }
            }
        }

        // 解题推导结果展示
        solveResult?.let { result ->
            Spacer(modifier = Modifier.height(14.dp))

            // 1. 题型与答案卡片
            Card(
                modifier = Modifier.fillMaxWidth(),
                shape = RoundedCornerShape(12.dp),
                colors = CardDefaults.cardColors(containerColor = Color(0xFFE8F5E9))
            ) {
                Column(modifier = Modifier.padding(14.dp)) {
                    Text(
                        text = "🎯 题型: ${result.problemType}",
                        color = Color(0xFF2E7D32),
                        fontSize = 14.sp,
                        fontWeight = FontWeight.SemiBold
                    )
                    Spacer(modifier = Modifier.height(4.dp))
                    Text(
                        text = "最终答案: ${result.finalAnswer}",
                        color = Color(0xFF1B5E20),
                        fontSize = 17.sp,
                        fontWeight = FontWeight.Bold
                    )
                }
            }

            // 2. 识别到的几何条件与定理依据
            if (result.conditions.isNotEmpty() || result.theorems.isNotEmpty()) {
                Spacer(modifier = Modifier.height(10.dp))
                Card(
                    modifier = Modifier.fillMaxWidth(),
                    shape = RoundedCornerShape(10.dp),
                    colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surfaceVariant)
                ) {
                    Column(modifier = Modifier.padding(10.dp)) {
                        if (result.conditions.isNotEmpty()) {
                            Text(text = "📌 解析已知条件: ${result.conditions.joinToString(" | ")}", fontSize = 12.sp, color = Color.DarkGray)
                        }
                        if (result.theorems.isNotEmpty()) {
                            Text(text = "📖 应用定理依据: ${result.theorems.joinToString("; ")}", fontSize = 12.sp, color = MaterialTheme.colorScheme.primary)
                        }
                    }
                }
            }

            // 3. 详细形式化推导证明步骤
            Spacer(modifier = Modifier.height(12.dp))
            Text(
                text = "💡 纯端侧形式化定理推导步骤:",
                fontWeight = FontWeight.SemiBold,
                fontSize = 14.sp,
                modifier = Modifier.align(Alignment.Start)
            )

            Column(modifier = Modifier.fillMaxWidth().padding(top = 6.dp)) {
                result.steps.forEach { step ->
                    Text(
                        text = step,
                        fontSize = 13.sp,
                        modifier = Modifier
                            .fillMaxWidth()
                            .padding(vertical = 3.dp)
                            .background(Color(0xFFF7F7F7), RoundedCornerShape(6.dp))
                            .padding(8.dp)
                    )
                }
            }
        }
    }
}
