package com.marketingai.app.ui.components

import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.grid.GridCells
import androidx.compose.foundation.lazy.grid.LazyVerticalGrid
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.ChevronLeft
import androidx.compose.material.icons.filled.ChevronRight
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import com.marketingai.app.data.models.GeneratedPostResponse
import java.time.LocalDate
import java.time.YearMonth
import java.time.format.DateTimeFormatter
import java.time.format.TextStyle
import java.util.Locale

@Composable
fun CalendarView(
    posts: List<GeneratedPostResponse>,
    onPostClick: (GeneratedPostResponse) -> Unit,
    modifier: Modifier = Modifier
) {
    var currentMonth by remember { mutableStateOf(YearMonth.now()) }

    // Group posts by date
    val postsByDate = remember(posts) {
        posts.groupBy { post ->
            try {
                val dateStr = post.scheduledAt ?: post.createdAt
                LocalDate.parse(dateStr.take(10))
            } catch (e: Exception) {
                LocalDate.now()
            }
        }
    }

    Card(modifier = modifier.fillMaxWidth()) {
        Column(modifier = Modifier.padding(16.dp)) {
            // Month navigation
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically
            ) {
                IconButton(onClick = { currentMonth = currentMonth.minusMonths(1) }) {
                    Icon(Icons.Default.ChevronLeft, contentDescription = "Previous month")
                }
                Text(
                    text = "${currentMonth.month.getDisplayName(TextStyle.FULL, Locale.getDefault())} ${currentMonth.year}",
                    style = MaterialTheme.typography.titleMedium,
                    fontWeight = FontWeight.SemiBold
                )
                IconButton(onClick = { currentMonth = currentMonth.plusMonths(1) }) {
                    Icon(Icons.Default.ChevronRight, contentDescription = "Next month")
                }
            }

            Spacer(modifier = Modifier.height(8.dp))

            // Day of week headers
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceEvenly
            ) {
                listOf("Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun").forEach { day ->
                    Text(
                        text = day,
                        style = MaterialTheme.typography.labelSmall,
                        color = MaterialTheme.colorScheme.onSurfaceVariant,
                        textAlign = TextAlign.Center,
                        modifier = Modifier.weight(1f)
                    )
                }
            }

            Spacer(modifier = Modifier.height(8.dp))

            // Calendar grid
            val firstDayOfMonth = currentMonth.atDay(1)
            val startOffset = (firstDayOfMonth.dayOfWeek.value - 1) // Monday = 0
            val daysInMonth = currentMonth.lengthOfMonth()
            val totalCells = startOffset + daysInMonth

            LazyVerticalGrid(
                columns = GridCells.Fixed(7),
                modifier = Modifier.height(((totalCells / 7 + 1) * 44).dp),
                userScrollEnabled = false
            ) {
                // Empty cells for offset
                items(startOffset) {
                    Box(modifier = Modifier.size(40.dp))
                }

                // Day cells
                items(daysInMonth) { dayIndex ->
                    val day = dayIndex + 1
                    val date = currentMonth.atDay(day)
                    val dayPosts = postsByDate[date] ?: emptyList()
                    val isToday = date == LocalDate.now()

                    Box(
                        modifier = Modifier
                            .size(40.dp)
                            .clip(CircleShape)
                            .then(
                                when {
                                    isToday -> Modifier.background(
                                        MaterialTheme.colorScheme.primaryContainer
                                    )
                                    dayPosts.isNotEmpty() -> Modifier.background(
                                        MaterialTheme.colorScheme.secondaryContainer.copy(alpha = 0.5f)
                                    )
                                    else -> Modifier
                                }
                            )
                            .clickable(enabled = dayPosts.isNotEmpty()) {
                                dayPosts.firstOrNull()?.let { onPostClick(it) }
                            },
                        contentAlignment = Alignment.Center
                    ) {
                        Column(horizontalAlignment = Alignment.CenterHorizontally) {
                            Text(
                                text = day.toString(),
                                style = MaterialTheme.typography.bodySmall,
                                fontWeight = if (isToday) FontWeight.Bold else FontWeight.Normal,
                                color = if (isToday)
                                    MaterialTheme.colorScheme.onPrimaryContainer
                                else
                                    MaterialTheme.colorScheme.onSurface
                            )
                            if (dayPosts.isNotEmpty()) {
                                Box(
                                    modifier = Modifier
                                        .size(4.dp)
                                        .clip(CircleShape)
                                        .background(MaterialTheme.colorScheme.primary)
                                )
                            }
                        }
                    }
                }
            }
        }
    }
}
