package com.marketingai.app.ui.screens.schedule

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.marketingai.app.data.models.ScheduleConfigureRequest
import com.marketingai.app.data.models.ScheduleResponse
import com.marketingai.app.data.repository.ApiResult
import com.marketingai.app.data.repository.ScheduleRepository
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch
import javax.inject.Inject

data class ScheduleUiState(
    val schedules: List<ScheduleResponse> = emptyList(),
    val selectedDays: Set<Int> = emptySet(),
    val selectedPlatform: String = "instagram",
    val timeSlot: String = "09:00",
    val frequency: ScheduleFrequency = ScheduleFrequency.DAILY,
    val timezone: String = "UTC",
    val isLoading: Boolean = false,
    val isSaving: Boolean = false,
    val error: String? = null,
    val successMessage: String? = null,
    val suggestions: Map<String, List<String>> = emptyMap()
)

enum class ScheduleFrequency(val label: String, val days: List<Int>) {
    DAILY("Daily", listOf(0, 1, 2, 3, 4, 5, 6)),
    WEEKDAYS("Weekdays", listOf(0, 1, 2, 3, 4)),
    EVERY_OTHER_DAY("Every Other Day", listOf(0, 2, 4, 6)),
    CUSTOM("Custom", emptyList())
}

@HiltViewModel
class ScheduleViewModel @Inject constructor(
    private val scheduleRepository: ScheduleRepository
) : ViewModel() {

    private val _uiState = MutableStateFlow(ScheduleUiState())
    val uiState: StateFlow<ScheduleUiState> = _uiState.asStateFlow()

    init {
        loadSchedule()
        loadSuggestions()
    }

    fun loadSchedule() {
        viewModelScope.launch {
            _uiState.update { it.copy(isLoading = true, error = null) }

            when (val result = scheduleRepository.getCurrentSchedule(1)) {
                is ApiResult.Success -> {
                    _uiState.update {
                        it.copy(
                            schedules = result.data.schedules,
                            isLoading = false
                        )
                    }
                }
                is ApiResult.Error -> {
                    _uiState.update {
                        it.copy(isLoading = false, error = result.message)
                    }
                }
            }
        }
    }

    private fun loadSuggestions() {
        viewModelScope.launch {
            when (val result = scheduleRepository.getScheduleSuggestions(
                _uiState.value.selectedPlatform
            )) {
                is ApiResult.Success -> {
                    _uiState.update {
                        it.copy(suggestions = result.data.bestPostingTimes)
                    }
                }
                is ApiResult.Error -> { /* Non-critical, ignore */ }
            }
        }
    }

    fun selectPlatform(platform: String) {
        _uiState.update { it.copy(selectedPlatform = platform) }
        loadSuggestions()
    }

    fun toggleDay(day: Int) {
        _uiState.update { state ->
            val updated = if (day in state.selectedDays) {
                state.selectedDays - day
            } else {
                state.selectedDays + day
            }
            state.copy(selectedDays = updated, frequency = ScheduleFrequency.CUSTOM)
        }
    }

    fun setFrequency(frequency: ScheduleFrequency) {
        _uiState.update {
            it.copy(
                frequency = frequency,
                selectedDays = frequency.days.toSet()
            )
        }
    }

    fun setTimeSlot(time: String) {
        _uiState.update { it.copy(timeSlot = time) }
    }

    fun setTimezone(timezone: String) {
        _uiState.update { it.copy(timezone = timezone) }
    }

    fun saveSchedule() {
        viewModelScope.launch {
            _uiState.update { it.copy(isSaving = true, error = null) }

            val state = _uiState.value
            var allSuccess = true

            for (day in state.selectedDays) {
                val request = ScheduleConfigureRequest(
                    businessId = 1,
                    platform = state.selectedPlatform,
                    dayOfWeek = day,
                    timeSlot = state.timeSlot,
                    timezone = state.timezone
                )

                when (scheduleRepository.configureSchedule(request)) {
                    is ApiResult.Success -> { /* continue */ }
                    is ApiResult.Error -> { allSuccess = false }
                }
            }

            if (allSuccess) {
                _uiState.update {
                    it.copy(
                        isSaving = false,
                        successMessage = "Schedule saved successfully"
                    )
                }
                loadSchedule()
            } else {
                _uiState.update {
                    it.copy(
                        isSaving = false,
                        error = "Some schedule slots failed to save"
                    )
                }
            }
        }
    }

    fun dismissMessage() {
        _uiState.update { it.copy(successMessage = null, error = null) }
    }
}
