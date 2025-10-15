# Video Library - User Guide

## Welcome to Your Video Library! 📚

Your video library is where all your uploaded videos live. Think of it as your personal video collection, organized and ready for exploration with BRI!

## Getting to the Library

### From Anywhere in BRI
1. Look at the sidebar on the left
2. Click the **"📚 Video Library"** button
3. Voilà! You're in your library

## Understanding Your Library

### What You'll See

#### Statistics Dashboard
At the top, you'll see quick stats about your collection:
- **Total Videos**: How many videos you've uploaded
- **Ready to Chat**: Videos that are fully processed and ready for questions
- **Processing**: Videos currently being analyzed
- **Upload New**: Quick button to upload more videos

#### Search & Filter Bar
Below the stats, you'll find tools to find specific videos:
- **Search Box** (🔍): Type any part of a video's filename
- **Status Filter**: Show only videos with a specific status
  - All: Show everything
  - Ready: Only fully processed videos
  - Processing: Videos being analyzed right now
  - Pending: Videos waiting to be processed
  - Error: Videos that had processing issues

#### Video Grid
Your videos are displayed in a beautiful 3-column grid. Each video card shows:
- **Thumbnail**: A preview image from your video
- **Filename**: The name of your video (shortened if too long)
- **Duration**: How long the video is (e.g., "2:35")
- **Status**: Processing status with a helpful emoji
  - ⏳ Pending: Waiting to be processed
  - ⚙️ Processing: Being analyzed right now
  - ✅ Ready: All set for chatting!
  - ❌ Error: Something went wrong
- **Upload Date**: When you uploaded it (e.g., "2 hours ago")
- **Action Buttons**: What you can do with this video

## Working with Videos

### Chatting with a Video
Want to ask questions about a video?

1. Find the video in your library
2. Click the **"💬 Chat"** button on its card
3. You'll be taken to the chat interface
4. Start asking questions!

**Tip**: Videos with ✅ Ready status work best for chatting!

### Deleting a Video
Need to remove a video?

1. Find the video you want to delete
2. Click the **"🗑️ Delete"** button
3. A confirmation dialog appears asking "⚠️ Are you sure?"
4. Click **"✅ Yes"** to confirm deletion
5. Click **"❌ No"** to cancel

**Important**: Deleting a video removes:
- The video file itself
- All extracted frames
- All processing results
- All conversation history
- This action cannot be undone!

### Uploading New Videos
Ready to add more videos?

1. Click the **"📤 Upload New"** button in the stats bar
2. You'll return to the welcome screen
3. Upload your video using drag-and-drop
4. Come back to the library to see it!

## Searching for Videos

### Using the Search Box
1. Click in the search box (🔍)
2. Type any part of the filename you're looking for
3. The grid updates instantly to show matching videos
4. Clear the search to see all videos again

**Examples**:
- Search "meeting" to find all meeting videos
- Search "2024" to find videos from 2024
- Search ".mp4" to find all MP4 files

### Using Status Filters
1. Click the status dropdown (shows "All" by default)
2. Select a status:
   - **All**: Show every video
   - **Ready**: Only show videos ready for chatting
   - **Processing**: See what's being analyzed
   - **Pending**: Videos waiting in queue
   - **Error**: Videos that need attention
3. The grid updates to show only matching videos

**Tip**: Combine search and filter! Search for "meeting" and filter by "Ready" to find all processed meeting videos.

## Understanding Video Status

### ⏳ Pending
- Video is uploaded but not yet processed
- BRI hasn't analyzed it yet
- You can't chat with it yet
- It will start processing soon

### ⚙️ Processing
- BRI is currently analyzing the video
- Extracting frames, captions, audio, and objects
- This can take a few minutes depending on video length
- Check back soon!

### ✅ Ready
- Video is fully processed
- All analysis complete
- Ready for chatting!
- Click "💬 Chat" to start asking questions

### ❌ Error
- Something went wrong during processing
- The video might be corrupted or in an unsupported format
- You can try deleting and re-uploading
- Or contact support if the problem persists

## Tips & Tricks

### Organizing Your Videos
- Use descriptive filenames before uploading
- Include dates or topics in filenames (e.g., "2024-01-15-team-meeting.mp4")
- This makes searching easier later!

### Managing Your Collection
- Regularly delete videos you no longer need
- Keep your library organized and manageable
- Use filters to focus on specific types of videos

### Best Practices
- Wait for videos to reach "Ready" status before chatting
- Use search when you have many videos
- Check the statistics to see your collection at a glance
- Upload videos with clear, descriptive names

### Performance Tips
- Smaller videos process faster
- Keep videos under 500MB for best performance
- Delete old videos you no longer need
- Use supported formats: MP4, AVI, MOV, MKV

## Troubleshooting

### "No videos yet!"
- You haven't uploaded any videos
- Click "📤 Upload Video" to get started
- Upload your first video from the welcome screen

### Video stuck in "Processing"
- Large videos take longer to process
- Wait a few more minutes
- Refresh the page to check status
- If stuck for over 10 minutes, try re-uploading

### Video shows "Error" status
- The video file might be corrupted
- Format might not be fully supported
- Try deleting and re-uploading
- Ensure video is under 500MB

### Thumbnail not showing
- Thumbnail generation might have failed
- You'll see a placeholder icon (🎬) instead
- This doesn't affect functionality
- You can still chat with the video

### Search not finding videos
- Check your spelling
- Try searching for just part of the name
- Clear filters and try again
- Make sure the video exists in your library

### Can't delete a video
- Make sure you clicked "✅ Yes" in the confirmation
- Check if you have permission to delete files
- Try refreshing the page
- Contact support if problem persists

## Empty State

### When You Have No Videos
If your library is empty, you'll see:
- A friendly message: "No videos yet!"
- An encouraging note from BRI
- A big "📤 Upload Video" button
- Click it to upload your first video!

## Keyboard Shortcuts

Currently, the video library uses mouse/touch interactions. Keyboard shortcuts may be added in future updates!

## Mobile Experience

The video library works on mobile devices:
- Grid adjusts to screen size
- Touch-friendly buttons
- Swipe to scroll through videos
- All features available on mobile

## Privacy & Data

### What's Stored
- Video files in your local data folder
- Thumbnails in cache folder
- Processing results in database
- Conversation history per video

### What Happens When You Delete
- All video data is removed
- Thumbnails are deleted
- Processing results are cleared
- Conversation history is erased
- This is permanent and cannot be undone

### Data Location
All data is stored locally on your machine:
- Videos: `data/videos/`
- Thumbnails: `data/cache/{video_id}/`
- Database: `data/bri.db`

## Getting Help

### Need Assistance?
- Check this guide for common questions
- Review the troubleshooting section
- Check the main README for setup help
- Contact support for technical issues

### Feedback
We'd love to hear from you!
- What features would you like?
- How can we improve the library?
- Any bugs or issues to report?

## What's Next?

After exploring your library:
1. **Select a video** to start chatting
2. **Ask questions** about your video content
3. **Explore features** like timestamp navigation
4. **Upload more videos** to build your collection

---

**Remember**: Your video library is your personal space to organize and explore your video content with BRI. Take your time, experiment with features, and enjoy the experience! 💜

Happy exploring! 🎬✨
