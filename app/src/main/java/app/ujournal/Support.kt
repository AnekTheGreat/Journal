package app.ujournal

import android.content.Context
import android.content.Intent
import android.net.Uri
import android.widget.Toast

/**
 * The tip jar.
 *
 * SideCut takes tips through Stripe Payment Links: one fixed amount per link, paid on a card page
 * Stripe hosts, opened in the browser. These are the same five amounts and the same five links, so
 * there is one place in the world that knows them.
 *
 * Nothing here is a key or a secret: a Payment Link is a public URL. The app never touches a card
 * number, and no tip unlocks anything - the journal behaves the same whether you tip or not, which
 * is why there is no receipt to check.
 */
object Support {

    /** dollars -> Stripe Payment Link, in the same order SideCut's Donate tab lists them. */
    val LINKS: List<Pair<Int, String>> = listOf(
        2 to "https://buy.stripe.com/eVqcN48Yn37BeBOagIdMI00",
        5 to "https://buy.stripe.com/28E4gyb6vfUn1P2dsUdMI01",
        10 to "https://buy.stripe.com/4gM4gy5Mb8rVbpC1KcdMI02",
        25 to "https://buy.stripe.com/6oUdR8fmLaA351e1KcdMI03",
        50 to "https://buy.stripe.com/4gM8wOb6v23x8dqcoQdMI04"
    )

    fun label(dollars: Int): String = "Tip \$$dollars"

    /** Hand the hosted page to the browser; the payment happens there, not in the app. */
    fun open(ctx: Context, url: String) {
        try {
            ctx.startActivity(
                Intent(Intent.ACTION_VIEW, Uri.parse(url))
                    .addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
            )
        } catch (e: Exception) {
            Toast.makeText(ctx, "No browser on this phone", Toast.LENGTH_SHORT).show()
        }
    }
}
