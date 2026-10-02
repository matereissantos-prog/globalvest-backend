package com.globalvest.app

import android.graphics.Color
import android.os.Bundle
import android.view.Gravity
import android.widget.Button
import android.widget.LinearLayout
import android.widget.ScrollView
import android.widget.TextView
import androidx.appcompat.app.AppCompatActivity
import java.net.URL
import javax.net.ssl.HttpsURLConnection

class MainActivity : AppCompatActivity() {
    private lateinit var status: TextView

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        val root = LinearLayout(this).apply {
            orientation = LinearLayout.VERTICAL
            setPadding(40, 56, 40, 40)
            setBackgroundColor(Color.rgb(245,247,251))
        }
        root.addView(TextView(this).apply { text="GLOBALVEST"; textSize=26f; setTextColor(Color.rgb(8,17,31)) })
        root.addView(TextView(this).apply { text="Android Connected Beta 3.5"; textSize=18f; setPadding(0,12,0,20) })
        root.addView(TextView(this).apply { text="PAPER TRADING • R$ 10.000 fictícios\nDinheiro real desativado"; textSize=16f; setTextColor(Color.rgb(20,90,180)); setPadding(0,10,0,24) })
        status = TextView(this).apply { text="Servidor: ainda não testado"; textSize=16f; setPadding(0,18,0,18) }
        root.addView(status)
        root.addView(Button(this).apply { text="Testar conexão segura"; setOnClickListener { testHealth() } })
        root.addView(TextView(this).apply { text="\nEsta versão é somente demonstrativa. Nenhuma ordem chega a uma corretora e nenhum dinheiro real é movimentado."; textSize=14f })
        setContentView(ScrollView(this).apply { addView(root) })
    }

    private fun testHealth() {
        status.text="Conectando ao servidor..."
        Thread {
            try {
                val conn=(URL(BuildConfig.API_BASE_URL + "/health").openConnection() as HttpsURLConnection).apply {
                    requestMethod="GET"; connectTimeout=65000; readTimeout=65000
                }
                val code=conn.responseCode
                val body=conn.inputStream.bufferedReader().use { it.readText() }
                runOnUiThread { status.text = if (code in 200..299 && body.contains("PAPER")) "Servidor GlobalVest ONLINE ✓\nModo PAPER confirmado" else "Servidor respondeu, mas precisa de validação\nHTTP $code" }
            } catch (e: Exception) {
                runOnUiThread { status.text="Não foi possível conectar agora. No plano gratuito, o servidor pode levar cerca de 1 minuto para acordar. Tente novamente." }
            }
        }.start()
    }
}
