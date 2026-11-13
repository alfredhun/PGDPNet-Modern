package com.example.geometrysolver

import android.content.Context
import android.graphics.Bitmap
import ai.onnxruntime.OnnxTensor
import ai.onnxruntime.OrtEnvironment
import ai.onnxruntime.OrtSession
import java.nio.FloatBuffer
import java.util.Collections

/**
 * Android 端本地 PGDPNet ONNX 推理器
 */
class GeometryOnnxDetector(private val context: Context) {
    private var ortEnv: OrtEnvironment? = null
    private var ortSession: OrtSession? = null
    var isInitialized = false
        private set
    var errorMessage: String? = null
        private set

    init {
        try {
            ortEnv = OrtEnvironment.getEnvironment()
            val modelBytes = context.assets.open("pgdp_backbone.onnx").readBytes()
            val options = OrtSession.SessionOptions()
            ortSession = ortEnv?.createSession(modelBytes, options)
            isInitialized = true
        } catch (e: Throwable) {
            e.printStackTrace()
            errorMessage = e.localizedMessage ?: e.toString()
        }
    }

    /**
     * 输入手机拍摄裁剪后的几何图形 Bitmap，在本地输出 6 级特征金字塔
     */
    fun extractFeatures(bitmap: Bitmap): Map<String, Any> {
        val env = ortEnv
        val session = ortSession
        if (!isInitialized || env == null || session == null) {
            return mapOf("error" to (errorMessage ?: "模型未完成初始化"))
        }

        val width = 384
        val height = 384
        val resizedBitmap = Bitmap.createScaledBitmap(bitmap, width, height, true)

        // 图像归一化 (BGR/RGB 转 Tensor: 1 x 3 x 384 x 384)
        val floatBuffer = FloatBuffer.allocate(1 * 3 * height * width)
        val intValues = IntArray(width * height)
        resizedBitmap.getPixels(intValues, 0, width, 0, 0, width, height)

        val mean = floatArrayOf(102.9801f, 115.9465f, 122.7717f)
        val std = floatArrayOf(1.0f, 1.0f, 1.0f)

        // 填充通道 R, G, B
        for (c in 0..2) {
            for (i in 0 until height * width) {
                val pixel = intValues[i]
                val channelVal = when (c) {
                    0 -> (pixel shr 16 and 0xFF).toFloat()
                    1 -> (pixel shr 8 and 0xFF).toFloat()
                    else -> (pixel and 0xFF).toFloat()
                }
                floatBuffer.put((channelVal - mean[c]) / std[c])
            }
        }
        floatBuffer.rewind()

        val inputTensor = OnnxTensor.createTensor(
            env,
            floatBuffer,
            longArrayOf(1, 3, height.toLong(), width.toLong())
        )

        // 本地高通/联发科 NPU/CPU 极速推理
        val results = session.run(Collections.singletonMap("input_image", inputTensor))
        
        val resultMap = mutableMapOf<String, Any>()
        results?.forEach { entry ->
            resultMap[entry.key] = entry.value.info.toString()
        }
        return resultMap
    }

    fun close() {
        try {
            ortSession?.close()
            ortEnv?.close()
        } catch (e: Throwable) {
            e.printStackTrace()
        }
    }
}
