package studio.jedl.app.content

import org.junit.Assert.*
import org.junit.Test
import studio.jedl.app.SceneObjectInstance

class AssetReferenceValidatorTest {
    private val hash = "a".repeat(64)
    private val asset = ContentAsset("library:asset", "Asset", "Props", ContentKind.OBJECT,
        "library", "/private/asset.png", 32, 32, hash, "1.0.0", installed = true)

    @Test fun exactBankVersionAndHashResolve() {
        val reference = SceneObjectInstance("library:asset", 0f, 0f, bankId = "library",
            assetSha256 = hash, packageVersion = "1.0.0")
        assertTrue(AssetReferenceValidator.matches(reference, asset))
    }

    @Test fun changedHashOrPackageVersionIsReportedAsMissingRevision() {
        val reference = SceneObjectInstance("library:asset", 0f, 0f, bankId = "library",
            assetSha256 = hash, packageVersion = "1.0.0")
        assertFalse(AssetReferenceValidator.matches(reference, asset.copy(sha256 = "b".repeat(64))))
        assertFalse(AssetReferenceValidator.matches(reference, asset.copy(packageVersion = "2.0.0")))
    }

    @Test fun legacyReferencesRemainReadableWithoutInventingFingerprints() {
        val reference = SceneObjectInstance("library:asset", 0f, 0f)
        assertTrue(AssetReferenceValidator.matches(reference, asset))
    }
}
