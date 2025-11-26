# 🎯 AI Scheduler Demo Guide

## 🚀 Quick Start

### 1. Open the App
Navigate to: **http://localhost:4200**

### 2. Connect Your Calendar
- Click **"Connecter Google Calendar"**
- Or use **"Continuer en mode démo"** for testing

### 3. Open Task Panel
- Click the **"Add Tasks"** button in the top navigation
- A panel slides in from the right

---

## 🎨 Demo Scenarios

### Scenario 1: Simple Daily Planning
**Type this:**
```
today I want to have breakfast and study
```

**What happens:**
1. AI detects: `scope = today`
2. Extracts 2 tasks:
   - Breakfast (30min, high priority, morning preference)
   - Study (90min, high priority, morning preference)
3. Places them optimally:
   - 🥐 **8:00-8:30**: Breakfast
   - 📚 **9:00-10:30**: Study

**Hover over tasks** to see explanations like:
- "Optimal breakfast time for morning energy"
- "Peak focus hours for deep work and complex tasks"

---

### Scenario 2: Full Day Planning
**Type this:**
```
I want to have breakfast, study for 2 hours, go to the gym, and visit a friend
```

**AI Schedule:**
- 🥐 **8:00-8:30**: Breakfast
  - *"Optimal breakfast time for morning energy"*
- 📚 **9:00-11:00**: Study
  - *"Peak focus hours for deep work and complex tasks"*
- 🏋️ **17:00-18:00**: Gym
  - *"Evening workout helps decompress after work"*
- 👥 **18:30-20:00**: Visit friend
  - *"Perfect time for social activities"*

---

### Scenario 3: Tomorrow Planning
**Type this:**
```
tomorrow I need to exercise and have lunch with colleagues
```

**AI Schedule (for tomorrow):**
- 🏋️ **7:30-8:30**: Exercise
  - *"Morning workout boosts metabolism and energy"*
- 🍽️ **12:30-13:30**: Lunch with colleagues
  - *"Natural midday break for energy replenishment"*

---

### Scenario 4: Weekly Planning
**Type this:**
```
this week I have to finish my project and exercise 3 times
```

**AI distributes across the week:**
- Mon 9:00: Project work (2h)
- Mon 17:00: Exercise (1h)
- Wed 9:00: Project work (2h)
- Wed 17:00: Exercise (1h)
- Fri 17:00: Exercise (1h)

---

## 🎯 Key Features to Test

### 1. **Hover Tooltips**
Hover over any scheduled task to see:
```
┌─────────────────────────────────────┐
│ 🤖 AI Explanation                   │
│ Peak focus hours for deep work and  │
│ complex tasks • High priority task  │
│ scheduled during peak hours         │
└─────────────────────────────────────┘
```

### 2. **Priority Colors**
- 🔴 **Red**: High priority (meals, urgent tasks)
- 🟡 **Amber**: Medium priority (normal tasks)
- 🔵 **Blue**: Low priority (leisure)

### 3. **Drag & Drop**
- Click and drag any task to reschedule
- Drop it in a new time slot
- AI maintains duration

### 4. **Real Calendar Integration**
- Your Google Calendar events appear as blue blocks
- AI schedules around them automatically
- No conflicts!

---

## 🧪 Test the AI Intelligence

### Test 1: Context Awareness
**Input:** "I want to have dinner and breakfast"

**Expected:** 
- Breakfast → Morning (8:00)
- Dinner → Evening (19:00)

**Why:** AI knows breakfast ≠ dinner time!

---

### Test 2: Priority Handling
**Input:** "I need to study urgently and maybe watch a movie"

**Expected:**
- Study → Morning peak hours (high priority)
- Movie → Evening (low priority)

**Why:** "urgently" = high priority, "maybe" = low priority

---

### Test 3: Duration Estimation
**Input:** "I want to have breakfast, lunch, and study"

**Expected:**
- Breakfast: 30min
- Lunch: 60min
- Study: 90min

**Why:** AI knows realistic durations for activities

---

### Test 4: Time Preferences
**Input:** "I want to exercise and work on my project"

**Expected:**
- Exercise → Morning (7:00) OR Evening (17:00)
- Project → Morning/Afternoon (9:00-17:00)

**Why:** Exercise fits energy peaks, deep work needs focus hours

---

## 🎬 Visual Demo Flow

```
1. Click "Add Tasks" 
   ↓
2. Panel slides in from right
   ↓
3. Type: "today I want to have breakfast and study"
   ↓
4. Click "Optimize" ✨
   ↓
5. AI processes (1-2 seconds)
   ↓
6. Tasks appear on calendar with colors
   ↓
7. Hover to see explanations
   ↓
8. Drag to reschedule if needed
   ↓
9. Close panel (X or click outside)
```

---

## 🔍 What to Look For

### ✅ Good AI Behavior
- Breakfast in morning (7:00-9:00)
- Study in peak hours (9:00-12:00)
- Lunch at midday (12:00-14:00)
- Exercise morning or evening
- Social activities afternoon/evening
- Dinner in evening (18:00-20:00)

### ❌ Bad AI Behavior (should NOT happen)
- Breakfast at night
- Dinner in morning
- Study at midnight
- Exercise at 2 AM

---

## 🎨 UI Elements

### Task Panel (Right Sidebar)
```
┌─────────────────────────────────┐
│ AI Task Scheduler          [X]  │
├─────────────────────────────────┤
│                                 │
│ [Text Area]                     │
│ Type your tasks in natural      │
│ language...                     │
│                                 │
│              [✨ Optimize]      │
│                                 │
├─────────────────────────────────┤
│ 📋 Parsed Tasks:                │
│  • Breakfast (30min, high)      │
│  • Study (90min, high)          │
│                                 │
├─────────────────────────────────┤
│ 🤖 AI Explanation:              │
│ Scheduled 2 tasks optimally     │
│ based on your calendar...       │
└─────────────────────────────────┘
```

### Calendar View
```
┌──────────────────────────────────────────┐
│ [Aujourd'hui] [<] [>]  Nov 2025  [Add Tasks] [Déco] │
├──────────────────────────────────────────┤
│ Mon    Tue    Wed    Thu    Fri          │
│                                          │
│ 08:00  🥐 Breakfast                      │
│        (hover: "Optimal breakfast...")   │
│                                          │
│ 09:00  📚 Study                          │
│        (hover: "Peak focus hours...")    │
│                                          │
│ 10:00  📅 Team Meeting (Google Cal)      │
│                                          │
└──────────────────────────────────────────┘
```

---

## 🎉 Success Criteria

After testing, you should see:

1. ✅ Tasks appear in logical time slots
2. ✅ Hover shows AI explanations
3. ✅ Colors match priorities
4. ✅ No conflicts with calendar events
5. ✅ Drag & drop works
6. ✅ Natural language understood correctly

---

## 🐛 Troubleshooting

### Tasks not appearing?
- Check browser console (F12)
- Verify backend is running (port 8001)
- Check for error messages

### Explanations not showing?
- Make sure you're hovering long enough
- Check if `explanation` field exists in response

### Wrong time slots?
- The AI learns from patterns
- Try more specific input: "breakfast at 8am"

---

## 📞 Support

If something doesn't work:
1. Check `backend/backend_log.txt`
2. Check `frontend/frontend_log.txt`
3. Open browser DevTools (F12) → Console
4. Look for error messages

---

**Enjoy your AI-powered scheduling! 🚀✨**





