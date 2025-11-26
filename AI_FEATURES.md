# 🤖 AI-Powered Smart Scheduling

## Overview
The AI scheduler now intelligently understands natural language, detects temporal context, and places tasks in optimal time slots with detailed explanations.

---

## ✨ Key Features

### 1. **Natural Language Understanding**
The AI parses spoken language and extracts:
- Task names
- Duration estimates
- Priority levels
- Time preferences
- Temporal scope (today, tomorrow, this week)

**Examples:**
```
"today I want to have breakfast and study"
→ AI detects: scope=today, 2 tasks (breakfast 30min, study 90min)

"tomorrow I need to go to the gym and visit a friend"
→ AI detects: scope=tomorrow, 2 tasks with appropriate durations

"this week I have to finish my project and exercise 3 times"
→ AI detects: scope=week, multiple tasks distributed across the week
```

---

### 2. **Context-Aware Time Placement**

The AI understands that certain activities belong at specific times:

#### Morning (7:00-12:00)
- ☕ **Breakfast**: 7:00-9:00 (morning energy boost)
- 🏋️ **Exercise**: 7:00-9:00 (metabolism boost)
- 📚 **Study/Deep Work**: 9:00-12:00 (peak cognitive performance)

#### Midday (12:00-14:00)
- 🍽️ **Lunch**: 12:00-14:00 (natural energy replenishment)

#### Afternoon (14:00-17:00)
- 💼 **Work/Projects**: 14:00-17:00 (good productivity window)
- 🤝 **Meetings**: 14:00-17:00 (collaborative activities)

#### Evening (17:00-21:00)
- 🏃 **Exercise**: 17:00-19:00 (decompress after work)
- 👥 **Social**: 17:00-21:00 (social gatherings)
- 🍽️ **Dinner**: 18:00-20:00 (family time)

---

### 3. **Smart Fit Scoring**

The AI calculates a "fit score" for each task placement based on:

1. **Efficiency**: Minimize wasted time in gaps
2. **Priority**: High-priority tasks get best slots
3. **Time Preference**: Match task to optimal time of day
4. **Context**: Breakfast in morning, dinner in evening, etc.

**Formula:**
```
fit_score = efficiency + priority_boost + time_boost

Where:
- efficiency = 1.0 - (waste / gap_duration)
- priority_boost = 0.33 (high), 0.2 (medium), 0.1 (low)
- time_boost = 0.6 (perfect match), -0.3 (mismatch)
```

---

### 4. **AI Explanations on Hover**

Each scheduled task includes an explanation visible on hover:

**Example Explanations:**
- 🥐 "Optimal breakfast time for morning energy"
- 📚 "Peak focus hours for deep work and complex tasks"
- 🏋️ "Morning workout boosts metabolism and energy"
- 🍽️ "Natural midday break for energy replenishment"
- 👥 "Perfect time for social activities"
- ⚡ "High priority task scheduled during peak hours"

---

### 5. **Real Calendar Integration**

The AI:
1. Fetches your real Google Calendar events
2. Identifies free time slots
3. Places tasks in gaps intelligently
4. Avoids conflicts with existing events

---

## 🎯 Usage Examples

### Example 1: Daily Planning
**Input:** "today I want to have breakfast, study for 2 hours, and visit a friend"

**AI Processing:**
1. Detects scope: `today`
2. Extracts tasks:
   - Breakfast (30min, high priority, morning)
   - Study (120min, high priority, morning/afternoon)
   - Visit friend (90min, medium priority, afternoon/evening)
3. Fetches calendar events
4. Finds free slots
5. Places tasks optimally:
   - 8:00-8:30: Breakfast (morning energy)
   - 9:00-11:00: Study (peak cognitive hours)
   - 15:00-16:30: Visit friend (afternoon social time)

### Example 2: Tomorrow Planning
**Input:** "tomorrow I need to go to the gym and have lunch with colleagues"

**AI Processing:**
1. Detects scope: `tomorrow` (shifts date by +1 day)
2. Places gym in morning (7:00-8:00)
3. Places lunch at midday (12:30-13:30)

### Example 3: Weekly Planning
**Input:** "this week I have to finish my project and exercise 3 times"

**AI Processing:**
1. Detects scope: `week`
2. Distributes tasks across the week
3. Places exercise sessions on Mon/Wed/Fri mornings
4. Schedules project work in peak productivity hours

---

## 🧠 AI Reasoning Examples

The AI generates contextual explanations:

### Breakfast at 8:00 AM
> "Optimal breakfast time for morning energy"

### Study Session at 9:30 AM
> "Peak focus hours for deep work and complex tasks • High priority task scheduled during peak hours"

### Gym at 7:00 AM
> "Morning workout boosts metabolism and energy"

### Lunch at 12:30 PM
> "Natural midday break for energy replenishment"

### Visit Friend at 17:00
> "Perfect time for social activities • Evening is ideal for social gatherings"

---

## 🎨 Visual Feedback

### Task Colors by Priority
- 🔴 **Red**: High priority (urgent, important)
- 🟡 **Amber**: Medium priority (normal tasks)
- 🔵 **Blue**: Low priority (optional, leisure)

### Hover Tooltip
When you hover over a scheduled task:
```
┌─────────────────────────────────┐
│ 🤖 AI Explanation               │
│ Peak focus hours for deep work  │
│ and complex tasks • High        │
│ priority task scheduled during  │
│ peak hours                      │
└─────────────────────────────────┘
```

---

## 🚀 Technical Implementation

### Backend (`ai_service.py`)
- GPT-4 powered natural language parsing
- Context-aware duration estimation
- Intelligent priority assignment
- Time preference detection

### Backend (`matching_service.py`)
- Smart fit scoring algorithm
- Context-aware time placement
- Explanation generation
- Conflict avoidance

### Frontend (`optimizer.ts`)
- Real calendar event integration
- Hover tooltip display
- Drag-and-drop rescheduling
- Visual priority indicators

---

## 📊 Performance

- **Parse Time**: ~500ms (GPT-4 API call)
- **Optimization Time**: ~100ms (local algorithm)
- **Total**: ~600ms from input to optimized schedule

---

## 🔮 Future Enhancements

1. **Multi-day optimization**: Spread tasks across multiple days
2. **Recurring tasks**: "gym every Monday/Wednesday/Friday"
3. **Travel time**: Account for commute between locations
4. **Energy levels**: Consider user's energy patterns
5. **Task dependencies**: "finish X before starting Y"
6. **Learning**: Adapt to user preferences over time

---

## 🎉 Try It Now!

1. Click "Add Tasks" button
2. Type: **"today I want to have breakfast, study, and visit a friend"**
3. Click "Optimize"
4. Hover over tasks to see AI explanations
5. Drag tasks to reschedule if needed

**The AI handles the Tetris. You focus on what matters.** ✨





