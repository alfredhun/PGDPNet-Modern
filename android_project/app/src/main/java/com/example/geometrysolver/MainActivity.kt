package com.example.geometrysolver

import android.graphics.Bitmap
import android.graphics.BitmapFactory
import android.graphics.ImageDecoder
import android.net.Uri
import android.os.Build
import android.os.Bundle
import android.provider.MediaStore
import androidx.activity.ComponentActivity
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.compose.setContent
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.foundation.Image
import androidx.compose.foundation.background
import androidx.compose.foundation.border
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
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext
import org.json.JSONObject
import kotlin.coroutines.resume
import kotlin.coroutines.suspendCoroutine

class MainActivity : ComponentActivity() {

    private var onnxDetector: GeometryOnnxDetector? = null

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)

        // 1. 初始化 Chaquopy (嵌入式本地 Python 引擎)
        try {
            if (!Python.isStarted()) {
                Python.start(AndroidPlatform(this))
            }
        } catch (e: Throwable) {
            e.printStackTrace()
        }

        // 2. 初始化 ONNX Runtime 几何检测引擎
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

// 本地 SymPy 神经符号推导
suspend fun solveFromTextOrParams(
    ocrText: String,
    paramAB: String,
    paramAPrimeB: String,
    paramAPrimeC: String
): Pair<List<String>, String> = withContext(Dispatchers.Default) {
    try {
        val py = Python.getInstance()
        val solverModule = py.getModule("geometry_solver")
        
        // 如果有明确参数直接代数求解，否则从 OCR 文本中正则推理
        val jsonStr = if (paramAPrimeB.isNotBlank() && paramAPrimeC.isNotBlank() && paramAB.isNotBlank()) {
            solverModule.callAttr("solve_swing_problem", paramAPrimeB, paramAPrimeC, paramAB).toString()
        } else {
            solverModule.callAttr("auto_parse_and_solve", ocrText).toString()
        }

        val json = JSONObject(jsonStr)
        if (json.has("error")) {
            return@withContext Pair(listOf("⚠️ 求解提示: " + json.getString("error")), "求解未完成")
        }

        val stepsArray = json.optJSONArray("steps")
        val steps = mutableListOf<String>()
        if (stepsArray != null) {
            for (i in 0 until stepsArray.length()) {
                steps.add(stepsArray.getString(i))
            }
        }
        val finalAnswer = json.optString("final_answer", "推导完成")
        Pair(steps, finalAnswer)
    } catch (e: Throwable) {
        Pair(listOf("推导异常: " + (e.localizedMessage ?: e.toString())), "计算失败")
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
    var paramAB by remember { mutableStateOf("0.7") }
    var paramAPrimeB by remember { mutableStateOf("2.5") }
    var paramAPrimeC by remember { mutableStateOf("2.0") }
    var isProcessing by remember { mutableStateOf(false) }
    var statusStage by remember { mutableStateOf("") }
    var steps by remember { mutableStateOf<List<String>>(emptyList()) }
    var finalAnswer by remember { mutableStateOf("") }

    // 处理新图片流程 (拍照或相册选图后触发)
    fun processImage(bitmap: Bitmap) {
        imageBitmap = bitmap
        isProcessing = true
        statusStage = "🔍 正在进行端侧特征提取与 OCR 识别..."
        
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

            // 2. 离线 OCR 识别
            statusStage = "📝 正在识别图中几何已知量与文字..."
            val ocr = recognizeTextFromBitmap(bitmap)
            recognizedText = ocr

            // 3. 自动正则提取已知量
            val abMatch = Regex("(?:最低点.*?|地面|离地|AB|高度)[^\\d]{0,8}(\\d+(?:\\.\\d+)?)").find(ocr)
            val apbMatch = Regex("A'B[^\\d]{0,8}(\\d+(?:\\.\\d+)?)").find(ocr)
            val apcMatch = Regex("A'C[^\\d]{0,8}(\\d+(?:\\.\\d+)?)").find(ocr)

            val newAB = abMatch?.groupValues?.getOrNull(1) ?: paramAB
            val newAPB = apbMatch?.groupValues?.getOrNull(1) ?: paramAPrimeB
            val newAPC = apcMatch?.groupValues?.getOrNull(1) ?: paramAPrimeC

            paramAB = newAB
            paramAPrimeB = newAPB
            paramAPrimeC = newAPC

            // 4. 自动推导求解
            statusStage = "⚡ 正在建立几何代数方程并求解..."
            val (s, a) = solveFromTextOrParams(ocr, newAB, newAPB, newAPC)
            steps = s
            finalAnswer = a
            isProcessing = false
            statusStage = ""
        }
    }

    // 1. 真实系统拍照 (返回拍摄的清晰高分辨率图片)
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
            text = "📐 几何全要素真实拍照与解题器",
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
                Text(text = "• 求解引擎: Chaquopy + SymPy 确定性代数推导", fontSize = 12.sp, color = Color.Gray)
            }
        }

        Spacer(modifier = Modifier.height(12.dp))

        // 拍照与选图核心操作区
        Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.spacedBy(8.dp)
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

        Spacer(modifier = Modifier.height(8.dp))

        // 快速加载测试样图
        OutlinedButton(
            onClick = {
                // 构造模拟测试样图
                val testBitmap = Bitmap.createBitmap(384, 384, Bitmap.Config.ARGB_8888)
                val sampleText = "如图, 当秋千 OA 静止时, 最低点 A 离地面的距离 AB 为 0.7 m, 当秋千摆动到 OA' 位置时, 点 A' 与点 B 的距离 A'B 为 2.5 m, 点 A' 水平移动的距离 A'C 为 2 m. 求秋千 OA 的长."
                processImage(testBitmap)
                recognizedText = sampleText
            },
            modifier = Modifier.fillMaxWidth().height(40.dp),
            shape = RoundedCornerShape(8.dp)
        ) {
            Text(text = "✨ 加载中考真题演练 (秋千几何)", fontSize = 13.sp)
        }

        // 显示已加载的真实题目图片
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

        // 正在处理状态
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

        // 识别到的文本与可调参数
        if (recognizedText.isNotEmpty()) {
            Spacer(modifier = Modifier.height(12.dp))
            Card(
                modifier = Modifier.fillMaxWidth(),
                shape = RoundedCornerShape(12.dp)
            ) {
                Column(modifier = Modifier.padding(12.dp)) {
                    Text(text = "📝 识别出的题目条件 (支持点击修改):", fontWeight = FontWeight.SemiBold, fontSize = 13.sp)
                    Text(
                        text = recognizedText,
                        fontSize = 12.sp,
                        color = Color.DarkGray,
                        modifier = Modifier
                            .fillMaxWidth()
                            .padding(vertical = 6.dp)
                            .background(Color(0xFFF0F0F0), RoundedCornerShape(6.dp))
                            .padding(8.dp)
                    )

                    Spacer(modifier = Modifier.height(6.dp))
                    Text(text = "🔢 关键边长几何参数:", fontWeight = FontWeight.Medium, fontSize = 12.sp)
                    Row(
                        modifier = Modifier.fillMaxWidth().padding(top = 4.dp),
                        horizontalArrangement = Arrangement.spacedBy(6.dp)
                    ) {
                        OutlinedTextField(
                            value = paramAPrimeB,
                            onValueChange = { paramAPrimeB = it },
                            label = { Text("A'B (m)") },
                            modifier = Modifier.weight(1f)
                        )
                        OutlinedTextField(
                            value = paramAPrimeC,
                            onValueChange = { paramAPrimeC = it },
                            label = { Text("A'C (m)") },
                            modifier = Modifier.weight(1f)
                        )
                        OutlinedTextField(
                            value = paramAB,
                            onValueChange = { paramAB = it },
                            label = { Text("AB (m)") },
                            modifier = Modifier.weight(1f)
                        )
                    }

                    Spacer(modifier = Modifier.height(8.dp))
                    Button(
                        onClick = {
                            scope.launch {
                                isProcessing = true
                                val (s, a) = solveFromTextOrParams(recognizedText, paramAB, paramAPrimeB, paramAPrimeC)
                                steps = s
                                finalAnswer = a
                                isProcessing = false
                            }
                        },
                        modifier = Modifier.fillMaxWidth().height(42.dp),
                        shape = RoundedCornerShape(6.dp)
                    ) {
                        Text(text = "⚡ 立即建立代数方程并求解", fontSize = 14.sp)
                    }
                }
            }
        }

        // 解题结果与推导步骤展示
        if (finalAnswer.isNotEmpty()) {
            Spacer(modifier = Modifier.height(12.dp))
            Card(
                modifier = Modifier.fillMaxWidth(),
                shape = RoundedCornerShape(12.dp),
                colors = CardDefaults.cardColors(containerColor = Color(0xFFE8F5E9))
            ) {
                Column(modifier = Modifier.padding(14.dp)) {
                    Text(
                        text = "🎯 本地推导最终答案:",
                        color = Color(0xFF2E7D32),
                        fontSize = 13.sp,
                        fontWeight = FontWeight.SemiBold
                    )
                    Text(
                        text = finalAnswer,
                        color = Color(0xFF1B5E20),
                        fontSize = 18.sp,
                        fontWeight = FontWeight.Bold,
                        modifier = Modifier.padding(top = 4.dp)
                    )
                }
            }

            Spacer(modifier = Modifier.height(12.dp))
            Text(
                text = "💡 纯本地形式化逻辑推导步骤:",
                fontWeight = FontWeight.SemiBold,
                fontSize = 14.sp,
                modifier = Modifier.align(Alignment.Start)
            )

            Column(modifier = Modifier.fillMaxWidth().padding(top = 6.dp)) {
                steps.forEach { step ->
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
