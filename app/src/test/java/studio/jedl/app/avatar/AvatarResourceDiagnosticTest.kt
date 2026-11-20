package studio.jedl.app.avatar

import org.junit.Assert.assertEquals
import org.junit.Test

class AvatarResourceDiagnosticTest {
    @Test fun reportsManifestPieceSlotBoneAndReason() {
        assertEquals(
            "Recurso de personaje no válido: manifiesto=styles/default/manifest.json; " +
                "pieza=forearm_skin_open_R; ranura=FOREARM_R; hueso=foreArmR; " +
                "causa=El ID de pieza debe estar en minúsculas",
            AvatarResourceDiagnostic.describe(
                "styles/default/manifest.json",
                "forearm_skin_open_R",
                "FOREARM_R",
                "foreArmR",
                "El ID de pieza debe estar en minúsculas"
            )
        )
    }
}
