package studio.jedl.app.content

import studio.jedl.app.SceneObjectInstance

/** Compares a persisted scene reference with the currently installed catalog entry. */
object AssetReferenceValidator {
    fun matches(reference: SceneObjectInstance, asset: ContentAsset): Boolean {
        if (reference.assetId != asset.id) return false
        if (reference.bankId.isNotBlank() && reference.bankId != asset.bankId) return false
        if (reference.packageVersion.isNotBlank() && reference.packageVersion != asset.packageVersion) return false
        if (reference.assetSha256.isNotBlank() && !reference.assetSha256.equals(asset.sha256, ignoreCase = true)) return false
        return true
    }
}
