package studio.jedl.app

import android.app.Application
import androidx.lifecycle.AndroidViewModel
import androidx.lifecycle.viewModelScope
import kotlinx.coroutines.CancellationException
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext
import studio.jedl.app.avatar.PieceLibrary
import studio.jedl.app.avatar.StylePackContract
import studio.jedl.app.content.ContentLibrary

sealed interface StudioStartupState {
    data object Loading : StudioStartupState
    data class Ready(
        val pieceLibrary: PieceLibrary,
        val contentLibrary: ContentLibrary
    ) : StudioStartupState
    data class Failed(val message: String) : StudioStartupState
    data object Cleared : StudioStartupState
}

/** Owns decoded startup libraries across Activity configuration changes. */
class StudioStartupViewModel(application: Application) : AndroidViewModel(application) {
    private val _state = MutableStateFlow<StudioStartupState>(StudioStartupState.Loading)
    val state = _state.asStateFlow()

    @Volatile
    var wasClearedForTest: Boolean = false
        private set

    init {
        viewModelScope.launch {
            try {
                val loaded = withContext(Dispatchers.IO) {
                    val pieces = PieceLibrary.load(getApplication(), StylePackContract.DEFAULT_STYLE)
                    try {
                        pieces to ContentLibrary.load(getApplication())
                    } catch (failure: Throwable) {
                        pieces.close()
                        throw failure
                    }
                }
                _state.value = StudioStartupState.Ready(loaded.first, loaded.second)
            } catch (cancelled: CancellationException) {
                throw cancelled
            } catch (failure: Exception) {
                _state.value = StudioStartupState.Failed(
                    failure.message ?: failure.javaClass.simpleName
                )
            }
        }
    }

    /** Transfers ownership of a successfully loaded style pack to this ViewModel. */
    fun adoptLibrary(next: PieceLibrary) {
        val current = _state.value as? StudioStartupState.Ready ?: return
        if (current.pieceLibrary === next) return
        _state.value = current.copy(pieceLibrary = next)
        current.pieceLibrary.close()
    }

    override fun onCleared() {
        val ready = _state.value as? StudioStartupState.Ready
        ready?.pieceLibrary?.close()
        ready?.contentLibrary?.close()
        _state.value = StudioStartupState.Cleared
        wasClearedForTest = true
        super.onCleared()
    }
}
