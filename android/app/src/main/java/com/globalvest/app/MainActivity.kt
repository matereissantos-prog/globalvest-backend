package com.globalvest.app

import android.graphics.Color
import android.os.Bundle
import android.text.InputType
import android.widget.*
import androidx.appcompat.app.AppCompatActivity
import org.json.JSONArray
import org.json.JSONObject
import java.net.URL
import javax.net.ssl.HttpsURLConnection

class MainActivity : AppCompatActivity() {
    private lateinit var root: LinearLayout
    private val navy = Color.rgb(8, 24, 48)
    private val blue = Color.rgb(24, 96, 190)
    private val green = Color.rgb(22, 132, 92)

    override fun onCreate(savedInstanceState: Bundle?) { super.onCreate(savedInstanceState); showWelcome() }

    private fun base(title: String, subtitle: String = "") {
        root = LinearLayout(this).apply { orientation=LinearLayout.VERTICAL; setPadding(42,52,42,48); setBackgroundColor(Color.rgb(247,249,252)) }
        root.addView(label("GLOBALVEST",28f,navy)); root.addView(label(title,24f,navy,18,4))
        if(subtitle.isNotBlank()) root.addView(label(subtitle,15f,Color.DKGRAY,0,22))
        setContentView(ScrollView(this).apply { addView(root) })
    }

    private fun label(text:String,size:Float,color:Int=Color.DKGRAY,top:Int=8,bottom:Int=8)=TextView(this).apply { this.text=text; textSize=size; setTextColor(color); setPadding(0,top,0,bottom) }
    private fun button(text:String,action:()->Unit)=Button(this).apply { this.text=text; isAllCaps=false; textSize=16f; setOnClickListener{action()} }
    private fun money(v:Double)="R$ ${String.format("%,.2f",v).replace(',', 'X').replace('.', ',').replace('X','.')}"

    private fun showWelcome() {
        base("MVP Beta 4.2", "Investimentos globais automatizados — ambiente de demonstração")
        root.addView(label("PAPER TRADING",18f,blue,12,2)); root.addView(label("R$ 10.000 fictícios • dinheiro real desativado",15f,blue,0,28))
        root.addView(button("Entrar no MVP"){showLogin()}); root.addView(button("Testar servidor"){testHealth()})
        root.addView(label("Nenhuma ordem desta versão chega a uma corretora. Nenhum dinheiro real é movimentado.",13f,Color.GRAY,28,0))
    }

    private fun showLogin() {
        base("Acessar conta de teste","Use dados fictícios nesta versão beta.")
        val email=EditText(this).apply { hint="E-mail de teste"; inputType=InputType.TYPE_TEXT_VARIATION_EMAIL_ADDRESS }
        val pass=EditText(this).apply { hint="Senha de teste"; inputType=InputType.TYPE_CLASS_TEXT or InputType.TYPE_TEXT_VARIATION_PASSWORD }
        root.addView(email); root.addView(pass); root.addView(button("Continuar"){showRisk()}); root.addView(button("Voltar"){showWelcome()})
    }

    private fun showRisk() {
        base("Seu perfil de risco","Escolha como você prefere equilibrar estabilidade e crescimento.")
        root.addView(button("Conservador"){showDashboard("Conservador",30,55,15)}); root.addView(button("Moderado"){showDashboard("Moderado",55,35,10)}); root.addView(button("Arrojado"){showDashboard("Arrojado",75,15,10)})
        root.addView(label("No MVP, o perfil controla somente uma carteira simulada. Antes de uso real, suitability e regras do parceiro regulado serão necessários.",13f,Color.GRAY,22,0))
    }

    private fun showDashboard(profile:String,growth:Int,defensive:Int,cash:Int) {
        base("Olá 👋","Dashboard • Perfil $profile"); root.addView(label("Patrimônio simulado",14f,Color.GRAY)); root.addView(label("R$ 10.000,00",30f,navy,0,4)); root.addView(label("PAPER • sem dinheiro real",14f,green,0,24))
        root.addView(label("Carteira recomendada",20f,navy)); root.addView(label("Crescimento global     $growth%\nDefensivos / renda fixa     $defensive%\nReserva / caixa     $cash%",16f,Color.DKGRAY,8,18))
        root.addView(button("Simular investimento de R$ 10.000"){requestPortfolio(profile)}); root.addView(button("Alterar perfil"){showRisk()}); root.addView(button("Verificar servidor"){testHealth()})
    }

    private fun requestPortfolio(profile:String) {
        Toast.makeText(this,"Consultando Portfolio Engine 4.2…",Toast.LENGTH_SHORT).show()
        Thread {
            try {
                val apiProfile=when(profile){"Conservador"->"conservative"; "Arrojado"->"aggressive"; else->"moderate"}
                val c=(URL(BuildConfig.API_BASE_URL+"/portfolio/recommendation").openConnection() as HttpsURLConnection).apply {
                    requestMethod="POST"; connectTimeout=65000; readTimeout=65000; doOutput=true; setRequestProperty("Content-Type","application/json")
                }
                val request=JSONObject().put("risk_profile",apiProfile).put("capital_brl",10000).toString()
                c.outputStream.bufferedWriter().use { it.write(request) }
                val code=c.responseCode
                val stream=if(code in 200..299)c.inputStream else c.errorStream
                val body=stream.bufferedReader().use { it.readText() }
                val json=JSONObject(body)
                val execution=json.optJSONObject("execution")
                if(code !in 200..299 || json.optString("mode")!="PAPER" || json.optBoolean("real_money",true) || json.optBoolean("live_market_data",true) || execution?.optBoolean("broker_order_sent",true)!=false || execution.optBoolean("direct_execution",true)) {
                    throw IllegalStateException("Resposta insegura")
                }
                val positions=json.getJSONArray("positions")
                runOnUiThread { showPortfolioFromApi(profile,positions,json.optDouble("total_allocated_brl",10000.0)) }
            } catch(e:Exception) { runOnUiThread { Toast.makeText(this,"Não foi possível consultar o Portfolio Engine. Tente novamente em instantes.",Toast.LENGTH_LONG).show() } }
        }.start()
    }

    private fun showPortfolioFromApi(profile:String, positions:JSONArray, total:Double) {
        base("Carteira simulada","Portfolio Engine 4.2 • Perfil $profile")
        root.addView(label("Total alocado",14f,Color.GRAY)); root.addView(label(money(total),28f,navy,0,20))

        for(i in 0 until positions.length()) {
            val p=positions.getJSONObject(i)
            val symbol=p.getString("symbol")
            val name=p.getString("name")
            val weight=p.getDouble("target_weight_pct")
            val price=p.getDouble("simulated_price_brl")
            val qty=p.getDouble("quantity")
            val value=p.getDouble("market_value_brl")
            root.addView(label("$symbol • $name",17f,navy,14,2))
            root.addView(label("Peso: ${weight}%\nPreço simulado: ${money(price)}\nQuantidade: ${String.format("%.4f",qty)}\nValor da posição: ${money(value)}",15f,Color.DKGRAY,0,10))
        }

        root.addView(label("Carteira recebida do servidor ✓",18f,green,24,4))
        root.addView(label("PAPER • preços sintéticos de demonstração • sem cotações ao vivo • nenhuma ordem enviada à corretora",14f,Color.DKGRAY,4,20))
        root.addView(button("Voltar ao dashboard"){showRisk()})
    }

    private fun testHealth() {
        Toast.makeText(this,"Conectando ao servidor…",Toast.LENGTH_SHORT).show()
        Thread { try {
            val c=(URL(BuildConfig.API_BASE_URL+"/health").openConnection() as HttpsURLConnection).apply { requestMethod="GET"; connectTimeout=65000; readTimeout=65000 }
            val body=c.inputStream.bufferedReader().use{it.readText()}; runOnUiThread { Toast.makeText(this,if(c.responseCode in 200..299&&body.contains("PAPER"))"Servidor ONLINE ✓ • PAPER confirmado" else "Servidor respondeu, validação pendente",Toast.LENGTH_LONG).show() }
        } catch(e:Exception){ runOnUiThread { Toast.makeText(this,"Servidor gratuito pode estar acordando. Tente novamente em instantes.",Toast.LENGTH_LONG).show() } } }.start()
    }
}
