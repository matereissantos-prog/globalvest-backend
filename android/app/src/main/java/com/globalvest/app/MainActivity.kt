package com.globalvest.app

import android.graphics.Color
import android.graphics.Canvas
import android.graphics.Paint
import android.view.View
import java.text.SimpleDateFormat
import java.util.Locale
import java.util.TimeZone
import android.os.Bundle
import android.text.InputType
import android.widget.*
import androidx.appcompat.app.AppCompatActivity
import org.json.JSONArray
import org.json.JSONObject
import java.net.URL
import java.util.UUID
import javax.net.ssl.HttpsURLConnection

class MainActivity : AppCompatActivity() {
    private lateinit var root: LinearLayout
    private val navy = Color.rgb(8, 24, 48)
    private val blue = Color.rgb(24, 96, 190)
    private val green = Color.rgb(22, 132, 92)
    private var currentProfile = "Moderado"
    private var accountBalance = 10000.0
    private val prefs by lazy { getSharedPreferences("globalvest_paper", MODE_PRIVATE) }
    private fun deviceKey():String {
        val saved=prefs.getString("device_key",null)
        if(saved!=null) return saved
        val created="gv-"+UUID.randomUUID().toString()
        prefs.edit().putString("device_key",created).apply()
        return created
    }
    private fun profileLabel(key:String)=when(key){"conservative"->"Conservador";"aggressive"->"Arrojado";else->"Moderado"}

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
    private fun signedMoney(v:Double)=(if(v>=0) "+" else "-")+money(kotlin.math.abs(v))
    private fun apiProfile(profile:String)=when(profile){"Conservador"->"conservative"; "Arrojado"->"aggressive"; else->"moderate"}

    private fun showWelcome() {
        base("MVP Beta 4.8", "Investimentos globais automatizados — ambiente de demonstração")
        root.addView(label("PAPER TRADING",18f,blue,12,2)); root.addView(label("R$ 10.000 fictícios • dinheiro real desativado",15f,blue,0,28))
        root.addView(button("Entrar no MVP"){recoverAccount()}); root.addView(button("Testar servidor"){testHealth()})
        root.addView(label("Nenhuma ordem desta versão chega a uma corretora. Nenhum dinheiro real é movimentado.",13f,Color.GRAY,28,0))
    }


    private fun recoverAccount() {
        base("Recuperando conta PAPER","Consultando sua conta de demonstração no servidor…")
        Thread {
            try {
                val c=(URL(BuildConfig.API_BASE_URL+"/demo/account/"+deviceKey()).openConnection() as HttpsURLConnection).apply {
                    requestMethod="GET";connectTimeout=65000;readTimeout=65000
                }
                val status=c.responseCode
                if(status==404) { c.disconnect();runOnUiThread { showRisk() };return@Thread }
                if(status!=200) throw IllegalStateException("HTTP $status")
                val json=JSONObject(c.inputStream.bufferedReader().use{it.readText()})
                c.disconnect()
                if(json.optString("mode")!="PAPER" || !json.optBoolean("persistent",false) || json.optString("device_key")!=deviceKey())
                    throw IllegalStateException("Conta PAPER inválida")
                val profile=profileLabel(json.optString("risk_profile"))
                val balance=json.getDouble("current_value_brl")
                accountBalance=balance
                runOnUiThread { showDashboardFor(profile);root.addView(label("Conta persistente recuperada ✓ • Patrimônio PAPER: "+money(balance),16f,green,18,4)) }
            } catch(e:Exception) {
                runOnUiThread {
                    base("Não foi possível recuperar a conta","Sua conta não foi apagada. Verifique a conexão e tente novamente.")
                    root.addView(button("Tentar novamente"){recoverAccount()})
                    root.addView(button("Voltar"){showWelcome()})
                }
            }
        }.start()
    }

    private fun createPaperAccount(profile:String) {
        base("Preparando conta PAPER","Salvando seu perfil de risco no servidor…")
        Thread {
            try {
                val c=(URL(BuildConfig.API_BASE_URL+"/demo/account").openConnection() as HttpsURLConnection).apply {
                    requestMethod="POST";connectTimeout=65000;readTimeout=65000;doOutput=true
                    setRequestProperty("Content-Type","application/json")
                }
                val payload=JSONObject().put("device_key",deviceKey()).put("risk_profile",apiProfile(profile))
                c.outputStream.bufferedWriter().use { it.write(payload.toString()) }
                val status=c.responseCode
                if(status !in 200..299) throw IllegalStateException("HTTP $status")
                val json=JSONObject(c.inputStream.bufferedReader().use{it.readText()})
                c.disconnect()
                if(json.optString("mode")!="PAPER" || !json.optBoolean("persistent",false) || json.optString("device_key")!=deviceKey())
                    throw IllegalStateException("Conta PAPER inválida")
                accountBalance=json.getDouble("current_value_brl")
                runOnUiThread { showDashboardFor(profile);root.addView(label("Conta de demonstração salva no servidor ✓",16f,green,18,4)) }
            } catch(e:Exception) {
                runOnUiThread {
                    base("Falha ao salvar conta","Não foi possível confirmar a conta persistente. Nenhum dinheiro real foi movimentado.")
                    root.addView(button("Tentar novamente"){createPaperAccount(profile)})
                    root.addView(button("Escolher outro perfil"){showRisk()})
                }
            }
        }.start()
    }

    private fun showLogin() {
        base("Acessar conta de teste","Use dados fictícios nesta versão beta.")
        val email=EditText(this).apply { hint="E-mail de teste"; inputType=InputType.TYPE_TEXT_VARIATION_EMAIL_ADDRESS }
        val pass=EditText(this).apply { hint="Senha de teste"; inputType=InputType.TYPE_CLASS_TEXT or InputType.TYPE_TEXT_VARIATION_PASSWORD }
        root.addView(email); root.addView(pass); root.addView(button("Continuar"){showRisk()}); root.addView(button("Voltar"){showWelcome()})
    }

    private fun showRisk() {
        base("Seu perfil de risco","Escolha como você prefere equilibrar estabilidade e crescimento.")
        root.addView(button("Conservador"){createPaperAccount("Conservador")}); root.addView(button("Moderado"){createPaperAccount("Moderado")}); root.addView(button("Arrojado"){createPaperAccount("Arrojado")})
        root.addView(label("No MVP, o perfil controla somente uma carteira simulada. Antes de uso real, suitability e regras do parceiro regulado serão necessários.",13f,Color.GRAY,22,0))
    }

    private fun showDashboard(profile:String,growth:Int,defensive:Int,cash:Int) {
        currentProfile=profile
        base("Olá 👋","Dashboard • Perfil $profile"); root.addView(label("Patrimônio PAPER registrado",14f,Color.GRAY)); root.addView(label(money(accountBalance),30f,navy,0,4)); root.addView(label("PAPER • sem dinheiro real",14f,green,0,24))
        root.addView(label("Carteira recomendada",20f,navy)); root.addView(label("Crescimento global     $growth%\nDefensivos / renda fixa     $defensive%\nReserva / caixa     $cash%",16f,Color.DKGRAY,8,18))
        root.addView(button("Ver carteira simulada"){requestPortfolio(profile)})
        root.addView(button("Desempenho / histórico"){requestHistory(profile)})
        root.addView(button("Registrar evolução simulada"){savePaperSnapshot(profile)})
        root.addView(button("Ver registros da conta"){loadPaperSnapshots(profile)})
        root.addView(button("Gráfico de evolução patrimonial"){loadPaperSnapshots(profile)})
        root.addView(button("Prévia de rebalanceamento"){requestRebalance(profile)})
        root.addView(button("Alterar perfil"){showRisk()}); root.addView(button("Verificar servidor"){testHealth()})
    }

    private fun post(path:String, profile:String):JSONObject {
        val c=(URL(BuildConfig.API_BASE_URL+path).openConnection() as HttpsURLConnection).apply {
            requestMethod="POST"; connectTimeout=65000; readTimeout=65000; doOutput=true; setRequestProperty("Content-Type","application/json")
        }
        val request=JSONObject().put("risk_profile",apiProfile(profile)).put("capital_brl",10000).toString()
        c.outputStream.bufferedWriter().use { it.write(request) }
        val code=c.responseCode
        val stream=if(code in 200..299)c.inputStream else c.errorStream
        val body=stream.bufferedReader().use { it.readText() }
        if(code !in 200..299) throw IllegalStateException("HTTP $code")
        return JSONObject(body)
    }

    private fun paperSafe(json:JSONObject):Boolean = json.optString("mode")=="PAPER" && !json.optBoolean("real_money",true) && !json.optBoolean("live_market_data",true)

    private fun requestPortfolio(profile:String) {
        Toast.makeText(this,"Consultando Portfolio Engine…",Toast.LENGTH_SHORT).show()
        Thread { try {
            val json=post("/portfolio/recommendation",profile)
            val execution=json.optJSONObject("execution")
            if(!paperSafe(json) || execution?.optBoolean("broker_order_sent",true)!=false || execution.optBoolean("direct_execution",true)) throw IllegalStateException("Resposta insegura")
            val positions=json.getJSONArray("positions")
            runOnUiThread { showPortfolioFromApi(profile,positions,json.optDouble("total_allocated_brl",10000.0)) }
        } catch(e:Exception) { runOnUiThread { Toast.makeText(this,"Não foi possível consultar a carteira.",Toast.LENGTH_LONG).show() } } }.start()
    }

    private fun showPortfolioFromApi(profile:String, positions:JSONArray, total:Double) {
        base("Carteira simulada","Portfolio Engine • Perfil $profile")
        root.addView(label("Total alocado",14f,Color.GRAY)); root.addView(label(money(total),28f,navy,0,20))
        for(i in 0 until positions.length()) {
            val p=positions.getJSONObject(i)
            root.addView(label("${p.getString("symbol")} • ${p.getString("name")}",17f,navy,14,2))
            root.addView(label("Peso: ${p.getDouble("target_weight_pct")}%\nPreço simulado: ${money(p.getDouble("simulated_price_brl"))}\nQuantidade: ${String.format("%.4f",p.getDouble("quantity"))}\nValor da posição: ${money(p.getDouble("market_value_brl"))}",15f,Color.DKGRAY,0,10))
        }
        root.addView(label("Carteira recebida do servidor ✓",18f,green,24,4)); root.addView(label("PAPER • preços sintéticos • nenhuma ordem enviada à corretora",14f,Color.DKGRAY,4,20)); root.addView(button("Voltar ao dashboard"){showDashboardFor(profile)})
    }


    private fun savePaperSnapshot(profile:String) {
        base("Atualizando conta PAPER","Registrando uma avaliação com preços sintéticos…")
        Thread { try {
            val json=post("/demo/account/"+deviceKey()+"/snapshot",profile)
            if(json.optString("mode")!="PAPER" || json.optBoolean("real_money",true) || json.optString("status")!="SAVED" || json.optString("device_key")!=deviceKey()) throw IllegalStateException("Resposta inválida")
            accountBalance=json.getDouble("current_value_brl")
            runOnUiThread { showDashboardFor(profile);root.addView(label("Snapshot simulado salvo ✓",17f,green,18,4)) }
        } catch(e:Exception) { runOnUiThread {
            base("Falha ao registrar","O servidor não confirmou o snapshot. Confira os registros antes de tentar novamente.")
            root.addView(button("Ver registros"){loadPaperSnapshots(profile)})
            root.addView(button("Voltar"){showDashboardFor(profile)})
        } } }.start()
    }

    private fun loadPaperSnapshots(profile:String) {
        base("Registros da conta PAPER","Consultando snapshots persistentes…")
        Thread { try {
            val c=(URL(BuildConfig.API_BASE_URL+"/demo/account/"+deviceKey()+"/snapshots").openConnection() as HttpsURLConnection).apply { requestMethod="GET";connectTimeout=65000;readTimeout=65000 }
            if(c.responseCode!=200) throw IllegalStateException("HTTP "+c.responseCode)
            val json=JSONObject(c.inputStream.bufferedReader().use { it.readText() })
            c.disconnect()
            if(json.optString("device_key")!=deviceKey()) throw IllegalStateException("Conta divergente")
            runOnUiThread {
                base("Registros persistentes","Histórico de atualizações da conta de demonstração")
                val items=json.getJSONArray("snapshots")
                val records=mutableListOf<Pair<String,Double>>()
                for(i in 0 until items.length()) {
                    val item=items.getJSONObject(i)
                    records.add(item.optString("created_at") to item.getDouble("portfolio_value_brl"))
                }
                records.sortBy { it.first }
                val initial=10000.0
                val chartRecords=records.filterIndexed { i, record -> i==0 || kotlin.math.abs(record.second-records[i-1].second)>0.005 }
                val values=listOf(initial)+chartRecords.map { it.second }
                val latest=values.last()
                val change=latest-initial
                val percent=change/initial*100
                root.addView(label("Evolução do patrimônio PAPER",20f,navy,10,6))
                root.addView(label("Inicial: "+money(initial)+" • Atual: "+money(latest),16f,navy))
                root.addView(label("Variação acumulada: "+signedMoney(change)+" ("+String.format(Locale("pt","BR"),"%+.2f",percent)+"%)",16f,if(change>=0)green else Color.RED))
                root.addView(label("Avaliações registradas: "+records.size,15f,Color.DKGRAY))
                root.addView(label("Pontos distintos no gráfico: "+chartRecords.size,14f,Color.DKGRAY))
                root.addView(PaperChart(values,chartRecords.lastOrNull()?.first).apply { minimumHeight=440 })
                if(records.isEmpty()) root.addView(label("Nenhum snapshot registrado ainda. O gráfico mostra apenas o capital inicial.",15f))
                for(i in records.indices.reversed()) {
                    val (date,value)=records[i]
                    val previous=if(i==0) initial else records[i-1].second
                    val delta=value-previous
                    val deltaPct=if(previous!=0.0) delta/previous*100 else 0.0
                    val displayDate=try {
                        val input=SimpleDateFormat("yyyy-MM-dd'T'HH:mm:ss",Locale.US).apply { timeZone=TimeZone.getTimeZone("UTC") }
                        val output=SimpleDateFormat("dd/MM/yyyy HH:mm",Locale("pt","BR")).apply { timeZone=TimeZone.getDefault() }
                        output.format(input.parse(date)!!)
                    } catch(e:Exception) { date }
                    root.addView(label(displayDate+" • Avaliação simulada\n"+money(value),16f,navy,12,2))
                    root.addView(label("Desde o registro anterior: "+signedMoney(delta)+" ("+String.format(Locale("pt","BR"),"%+.2f",deltaPct)+"%)",14f,if(delta>=0)green else Color.RED,0,12))
                }
                root.addView(button("Voltar ao dashboard"){showDashboardFor(profile)})
            }
        } catch(e:Exception) { runOnUiThread {
            base("Não foi possível carregar registros","Tente novamente quando o servidor estiver disponível.")
            root.addView(button("Tentar novamente"){loadPaperSnapshots(profile)})
            root.addView(button("Voltar"){showDashboardFor(profile)})
        } } }.start()
    }

    private inner class PaperChart(private val values:List<Double>,private val lastTimestamp:String?):View(this) {
        private val paint=Paint(Paint.ANTI_ALIAS_FLAG)
        override fun onDraw(canvas:Canvas) {
            super.onDraw(canvas)
            val left=80f;val right=width-25f;val top=35f;val bottom=height-75f
            val min=values.minOrNull() ?: 0.0
            val max=values.maxOrNull() ?: 1.0
            val padding=((max-min)*0.15).coerceAtLeast(50.0)
            val low=min-padding;val high=max+padding
            paint.color=Color.LTGRAY;paint.strokeWidth=2f
            for(i in 0..4) {
                val y=top+(bottom-top)*i/4f
                canvas.drawLine(left,y,right,y,paint)
                paint.color=Color.DKGRAY;paint.textSize=25f
                canvas.drawText(String.format(Locale("pt","BR"),"%.0f",high-(high-low)*i/4),4f,y+8f,paint)
                paint.color=Color.LTGRAY
            }
            paint.color=blue;paint.strokeWidth=5f;paint.style=Paint.Style.STROKE
            fun x(i:Int)=left+(right-left)*i/(values.size-1).coerceAtLeast(1).toFloat()
            fun y(v:Double)=(bottom-(v-low)/(high-low)*(bottom-top)).toFloat()
            if(values.size==1) canvas.drawCircle(x(0),y(values[0]),5f,paint)
            else for(i in 1 until values.size) canvas.drawLine(x(i-1),y(values[i-1]),x(i),y(values[i]),paint)
            paint.style=Paint.Style.FILL;paint.color=navy;paint.textSize=26f
            canvas.drawText("Início",left,bottom+40f,paint)
            val dateLabel=lastTimestamp?.take(10)?.split("-")?.let { if(it.size==3) it[2]+"/"+it[1] else "Atual" } ?: "Atual"
            canvas.drawText(dateLabel,right-85f,bottom+40f,paint)
        }
    }

    private fun requestHistory(profile:String) {
        Toast.makeText(this,"Carregando histórico…",Toast.LENGTH_SHORT).show()
        Thread { try { val json=post("/portfolio/history",profile); if(!paperSafe(json)) throw IllegalStateException("Resposta insegura"); runOnUiThread { showHistory(profile,json) } }
        catch(e:Exception){ runOnUiThread { Toast.makeText(this,"Não foi possível carregar o histórico.",Toast.LENGTH_LONG).show() } } }.start()
    }

    private fun showHistory(profile:String,json:JSONObject) {
        base("Desempenho simulado","Portfolio Engine ${json.optString("engine_version","4.3")} • Perfil $profile")
        val start=json.optDouble("starting_value_brl",10000.0); val current=json.optDouble("current_value_brl",start); val ret=json.optDouble("return_pct",0.0)
        root.addView(label("Valor inicial",14f,Color.GRAY)); root.addView(label(money(start),22f,navy,0,12)); root.addView(label("Valor atual simulado",14f,Color.GRAY)); root.addView(label(money(current),30f,navy,0,8)); root.addView(label("Retorno simulado: ${String.format("%.2f",ret)}%",18f,if(ret>=0)green else Color.RED,0,22))
        root.addView(label("Histórico PAPER recebido do servidor ✓",17f,green)); root.addView(label("Resultados simulados não representam garantia de rentabilidade futura.",13f,Color.GRAY,8,20)); root.addView(button("Voltar ao dashboard"){showDashboardFor(profile)})
    }

    private fun requestRebalance(profile:String) {
        Toast.makeText(this,"Calculando prévia…",Toast.LENGTH_SHORT).show()
        Thread { try { val json=post("/portfolio/rebalance-preview",profile); if(!paperSafe(json) || json.optString("action")!="PREVIEW_ONLY") throw IllegalStateException("Resposta insegura"); runOnUiThread { showRebalance(profile,json) } }
        catch(e:Exception){ runOnUiThread { Toast.makeText(this,"Não foi possível calcular a prévia.",Toast.LENGTH_LONG).show() } } }.start()
    }

    private fun showRebalance(profile:String,json:JSONObject) {
        base("Rebalanceamento","Prévia somente • nenhuma ordem será executada")
        root.addView(label("Patrimônio simulado",14f,Color.GRAY)); root.addView(label(money(json.optDouble("portfolio_value_brl",10000.0)),28f,navy,0,18))
        val drift=json.optJSONArray("drift") ?: JSONArray()
        for(i in 0 until drift.length()) { val d=drift.getJSONObject(i); val delta=d.optDouble("drift_pct",0.0); root.addView(label("${d.optString("symbol")}\nAlvo: ${d.optDouble("target_weight_pct")}% • Atual: ${d.optDouble("current_weight_pct")}%\nDesvio: ${if(delta>=0)"+" else ""}${String.format("%.2f",delta)} p.p.",16f,navy,10,8)) }
        root.addView(label("PREVIEW ONLY ✓",18f,green,20,4)); root.addView(label("O sistema apenas calcula os ajustes necessários. Dinheiro real e envio de ordens continuam desativados.",14f,Color.DKGRAY,4,20)); root.addView(button("Voltar ao dashboard"){showDashboardFor(profile)})
    }

    private fun showDashboardFor(profile:String) { when(profile){"Conservador"->showDashboard(profile,30,55,15);"Arrojado"->showDashboard(profile,75,15,10);else->showDashboard(profile,55,35,10)} }

    private fun testHealth() {
        Toast.makeText(this,"Conectando ao servidor…",Toast.LENGTH_SHORT).show()
        Thread { try { val c=(URL(BuildConfig.API_BASE_URL+"/health").openConnection() as HttpsURLConnection).apply { requestMethod="GET"; connectTimeout=65000; readTimeout=65000 }; val body=c.inputStream.bufferedReader().use{it.readText()}; runOnUiThread { Toast.makeText(this,if(c.responseCode in 200..299&&body.contains("PAPER"))"Servidor ONLINE ✓ • PAPER confirmado" else "Servidor respondeu, validação pendente",Toast.LENGTH_LONG).show() } } catch(e:Exception){ runOnUiThread { Toast.makeText(this,"Servidor gratuito pode estar acordando. Tente novamente em instantes.",Toast.LENGTH_LONG).show() } } }.start()
    }
}
