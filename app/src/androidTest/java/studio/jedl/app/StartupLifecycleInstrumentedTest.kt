package studio.jedl.app

import androidx.lifecycle.Lifecycle
import androidx.test.core.app.ActivityScenario
import androidx.test.ext.junit.runners.AndroidJUnit4
import kotlinx.coroutines.flow.first
import kotlinx.coroutines.runBlocking
import kotlinx.coroutines.withTimeout
import org.junit.Assert.assertSame
import org.junit.Assert.assertTrue
import org.junit.Test
import org.junit.runner.RunWith

@RunWith(AndroidJUnit4::class)
class StartupLifecycleInstrumentedTest {

    @Test
    fun startupLoadsBundledResourcesAndRetainsViewModelAcrossRecreation() {
        ActivityScenario.launch(MainActivity::class.java).use { scenario ->
            lateinit var firstViewModel: StudioStartupViewModel
            scenario.onActivity { activity ->
                firstViewModel = activity.startupViewModelForTest
            }

            val firstState = runBlocking {
                withTimeout(30_000) {
                    firstViewModel.state.first {
                        it is StudioStartupState.Ready || it is StudioStartupState.Failed
                    }
                }
            }
            assertTrue(
                "Startup failed while loading APK assets: " +
                    (firstState as? StudioStartupState.Failed)?.message,
                firstState is StudioStartupState.Ready
            )
            val readyBefore = firstState as StudioStartupState.Ready
            assertTrue(readyBefore.pieceLibrary.parts.isNotEmpty())
            assertTrue(readyBefore.contentLibrary.banks.isNotEmpty())

            scenario.recreate()

            scenario.onActivity { recreated ->
                assertSame(
                    "ViewModel must survive Activity configuration recreation",
                    firstViewModel,
                    recreated.startupViewModelForTest
                )
            }
            val readyAfter = runBlocking {
                withTimeout(5_000) {
                    firstViewModel.state.first { it is StudioStartupState.Ready }
                }
            } as StudioStartupState.Ready
            assertSame(
                "Piece library should not be decoded again on rotation",
                readyBefore.pieceLibrary,
                readyAfter.pieceLibrary
            )
            assertSame(
                "Content library should remain owned by the ViewModel",
                readyBefore.contentLibrary,
                readyAfter.contentLibrary
            )
        }
    }

    @Test
    fun destroyingActivityClearsItsViewModel() {
        val scenario = ActivityScenario.launch(MainActivity::class.java)
        lateinit var viewModel: StudioStartupViewModel
        scenario.onActivity { viewModel = it.startupViewModelForTest }
        runBlocking {
            withTimeout(30_000) {
                viewModel.state.first {
                    it is StudioStartupState.Ready || it is StudioStartupState.Failed
                }
            }
        }

        scenario.moveToState(Lifecycle.State.DESTROYED)
        assertTrue(
            "ViewModel.onCleared must run when Activity is permanently destroyed",
            viewModel.wasClearedForTest
        )
        scenario.close()
    }
}
