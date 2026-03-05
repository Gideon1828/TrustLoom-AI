# 🧪 Quick Test Guide - Steps 7.4 & 7.5

## 🚀 Quick Start

### 1. Start Backend API

```powershell
cd api
python main.py
```

**Expected:** Server starts at `http://localhost:8000`

### 2. Start Frontend Dev Server

```powershell
cd frontend
npm start
```

**Expected:** Browser opens at `http://localhost:3000`

---

## ✅ Test Scenarios

### Test 1: Normal Evaluation Flow ⭐

**Steps:**

1. Upload a PDF/DOCX resume
2. Enter GitHub URL: `https://github.com/yourusername`
3. Enter LinkedIn URL: `https://linkedin.com/in/yourusername`
4. Select experience level: "Mid Level"
5. (Optional) Enter portfolio URL
6. Click "Evaluate Trust Score"

**Expected Behavior:**

- ✅ Loading spinner appears immediately
- ✅ Status changes to "📄 Uploading resume..."
- ✅ Status changes to "🧠 Analyzing language quality with BERT AI..."
- ✅ Status changes to "🔮 Evaluating project patterns with LSTM..."
- ✅ Status changes to "🔗 Validating GitHub and LinkedIn profiles..."
- ✅ Status changes to "✅ Calculating final trust score..."
- ✅ Elapsed time counter increments (0s → 1s → 2s → ...)
- ✅ Estimated time shows "~30s"
- ✅ Results page displays with trust score

---

### Test 2: Retry Mechanism 🔄

**Option A: Stop Backend During Evaluation**

1. Start evaluation with valid data
2. **Quickly** stop backend (Ctrl+C in API terminal)
3. Watch the retry mechanism

**Expected Behavior:**

- ✅ Status changes to "🔄 Connection issue. Retrying (1/3)..."
- ✅ Wait 2 seconds
- ✅ Status changes to "🔄 Connection issue. Retrying (2/3)..."
- ✅ Wait 2 seconds
- ✅ Status changes to "🔄 Connection issue. Retrying (3/3)..."
- ✅ After 3rd retry fails, error alert appears
- ✅ Error: "Unable to connect to the server. Please ensure the API is running at http://localhost:8000"

**Option B: Invalid API URL**

1. Edit `InputForm.jsx`:
   ```javascript
   const API_BASE_URL = "http://localhost:9999"; // Wrong port
   ```
2. Submit form
3. Observe retry attempts

---

### Test 3: Validation Errors 🚫

**Test 3.1: Missing Resume**

1. Leave resume upload empty
2. Fill other fields
3. Click "Evaluate Trust Score"

**Expected:** Red error message: "Resume file is required"

**Test 3.2: Invalid File Type**

1. Try uploading a .txt or .jpg file
2. **Expected:** Error: "Only PDF and DOCX files are allowed"

**Test 3.3: Invalid GitHub URL**

1. Enter: `github.com/user` (missing https://)
2. Tab out of field
3. **Expected:** Error: "URL must start with http:// or https://"

**Test 3.4: Invalid LinkedIn URL**

1. Enter: `https://facebook.com/user` (wrong domain)
2. Tab out of field
3. **Expected:** Error: "Must be a valid LinkedIn URL"

**Test 3.5: Missing Experience Level**

1. Leave dropdown at "Select experience level"
2. Try submitting
3. **Expected:** Error: "Experience level is required"

---

### Test 4: Loading States Visual Check 🎨

**Focus on these visual elements:**

✅ **Spinner:**

- Large (60px)
- Smooth rotation
- Purple gradient border
- Centered position

✅ **Status Message:**

- Clear text with emoji
- Purple color (#5b21b6)
- Pulsing animation effect
- Changes at each stage

✅ **Time Indicators:**

- Two side-by-side displays
- "Elapsed: Xs" (increments every second)
- "Estimated: ~30s" (stays constant)
- Monospace font for numbers

✅ **Overall Panel:**

- Purple gradient background
- Smooth fade-in animation
- Rounded corners
- Centered content
- Professional appearance

---

### Test 5: Error Handling 🛡️

**Test 5.1: Server Error (500)**

1. Modify backend to return 500 error
2. Submit form
3. **Expected:** "Server error. Please try again later."

**Test 5.2: Validation Error (422)**

1. Send invalid data to API
2. **Expected:** "Validation error. Please check your inputs."

**Test 5.3: Network Timeout**

1. Use very slow network
2. Wait for timeout (30s for upload, 60s for evaluate)
3. **Expected:** Retry mechanism activates or timeout error

---

## 🎯 Success Criteria

### Step 7.4 Success ✅

- [ ] Loading spinner displays
- [ ] Status messages update at each stage
- [ ] Elapsed time counter works
- [ ] Estimated time displays (~30s)
- [ ] Loading panel has gradient background
- [ ] Animations are smooth
- [ ] Loading states clear after completion

### Step 7.5 Success ✅

- [ ] Form submits to backend API
- [ ] Successful evaluation shows results
- [ ] Errors display clear messages
- [ ] Retry mechanism works (max 3 attempts)
- [ ] 2-second delay between retries
- [ ] All HTTP error codes handled
- [ ] Connection errors handled
- [ ] Timeout errors handled

---

## 📸 Visual Checklist

### Before Submission:

![Form Ready]

- ✅ Resume uploaded (green checkmark)
- ✅ All URLs filled
- ✅ Experience level selected
- ✅ No validation errors
- ✅ "Evaluate Trust Score" button enabled

### During Evaluation:

![Loading State]

- ✅ Large purple spinner rotating
- ✅ Status message with emoji visible
- ✅ Elapsed time: 5s, 6s, 7s... (counting up)
- ✅ Estimated time: ~30s (constant)
- ✅ Purple gradient background
- ✅ "Please wait..." subtext

### After Success:

![Results Page]

- ✅ Trust score displayed (0-100)
- ✅ Risk level badge (GREEN/YELLOW/RED)
- ✅ Score breakdown visible
- ✅ Flags section populated
- ✅ "Analyze Another Resume" button

### After Error:

![Error Alert]

- ✅ Alert dialog appears
- ✅ Clear error message
- ✅ Error details included
- ✅ Loading states cleared
- ✅ Form ready for retry

---

## 🐛 Common Issues & Solutions

### Issue 1: Spinner doesn't appear

**Solution:** Check that `isLoading` prop is being set to `true`

### Issue 2: Status messages don't update

**Solution:** Verify `setLoadingStatus()` calls in `handleSubmit()`

### Issue 3: Elapsed time doesn't increment

**Solution:** Check that timer interval is created and not immediately cleared

### Issue 4: Retry doesn't work

**Solution:** Verify `apiCallWithRetry()` function is wrapping API calls

### Issue 5: Backend connection fails

**Solution:** Ensure backend is running at `http://localhost:8000`

```powershell
cd api
python main.py
```

### Issue 6: CORS errors in console

**Solution:** Check backend CORS configuration in `main.py`

---

## 🔍 Debugging Tips

### Check Browser Console:

```javascript
// Open DevTools (F12) and check Console tab
// Look for:
- "Evaluation error:" messages
- Network requests to localhost:8000
- Status updates being logged
```

### Check Network Tab:

```
1. Open DevTools (F12)
2. Go to Network tab
3. Submit form
4. Watch for:
   - POST /upload-resume (should return 200)
   - POST /evaluate (should return 200)
   - Check response data
```

### Check Backend Logs:

```powershell
# In API terminal, watch for:
- POST /upload-resume requests
- POST /evaluate requests
- Any error messages
```

---

## 📊 Performance Benchmarks

### Expected Times:

- **Resume Upload:** 1-3 seconds
- **BERT Analysis:** 5-10 seconds
- **LSTM Evaluation:** 5-10 seconds
- **Profile Validation:** 3-5 seconds
- **Total Time:** 15-35 seconds

### With Retries:

- **1 Retry:** +2 seconds delay
- **2 Retries:** +4 seconds delay
- **3 Retries:** +6 seconds delay
- **Max Time:** ~45-60 seconds (with all retries)

---

## ✅ Final Checklist

Before marking Steps 7.4 & 7.5 complete, verify:

### Functionality:

- [ ] Form submits successfully
- [ ] Loading states display correctly
- [ ] Status messages update
- [ ] Timers work (elapsed & estimated)
- [ ] Results display on success
- [ ] Errors display on failure
- [ ] Retry mechanism works
- [ ] All validation works

### Visual:

- [ ] Spinner rotates smoothly
- [ ] Colors match theme (purple)
- [ ] Animations are smooth
- [ ] Text is readable
- [ ] Layout is centered
- [ ] Responsive on mobile

### Error Handling:

- [ ] Connection errors caught
- [ ] Timeout errors caught
- [ ] Validation errors caught
- [ ] Server errors caught
- [ ] Clear error messages shown

### User Experience:

- [ ] Always know what's happening
- [ ] Never see technical errors
- [ ] Can retry after errors
- [ ] Loading states clear properly
- [ ] Smooth transitions

---

## 🎉 You're Done!

If all tests pass, **Steps 7.4 & 7.5 are complete!**

**Next:** Move to **Phase 8 - Testing & Validation**

---

**Test Date:** ****\_\_****  
**Tested By:** ****\_\_****  
**Status:** ⬜ PASS / ⬜ FAIL  
**Notes:** ********\_\_\_\_********
