// Dashboard-specific functionality

document.addEventListener('DOMContentLoaded', function() {
  // Initialize any charts on the dashboard
  initDashboardCharts();
  
  // Handle timetable navigation
  const timetableNavBtns = document.querySelectorAll('.timetable-nav-btn');
  if (timetableNavBtns.length > 0) {
    timetableNavBtns.forEach(btn => {
      btn.addEventListener('click', function() {
        const targetDay = this.dataset.day;
        
        // Hide all timetable sections
        const allDays = document.querySelectorAll('.timetable-day');
        allDays.forEach(day => day.classList.add('d-none'));
        
        // Show target day
        const targetSection = document.getElementById(`timetable-${targetDay}`);
        if (targetSection) {
          targetSection.classList.remove('d-none');
        }
        
        // Update active button
        timetableNavBtns.forEach(navBtn => navBtn.classList.remove('active'));
        this.classList.add('active');
      });
    });
    
    // Activate the current day by default
    const currentDayIndex = new Date().getDay(); // 0 = Sunday, 1 = Monday, etc.
    const daysOfWeek = ['sunday', 'monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday'];
    const currentDay = daysOfWeek[currentDayIndex];
    const defaultBtn = document.querySelector(`.timetable-nav-btn[data-day="${currentDay}"]`) || timetableNavBtns[0];
    
    if (defaultBtn) {
      defaultBtn.click();
    }
  }
});

// Initialize dashboard charts
function initDashboardCharts() {
  // Attendance overview chart
  const attendanceChartElement = document.getElementById('attendance-overview-chart');
  if (attendanceChartElement) {
    const presentCount = parseInt(attendanceChartElement.dataset.present || 0);
    const absentCount = parseInt(attendanceChartElement.dataset.absent || 0);
    const lateCount = parseInt(attendanceChartElement.dataset.late || 0);
    const excusedCount = parseInt(attendanceChartElement.dataset.excused || 0);
    
    const ctx = attendanceChartElement.getContext('2d');
    const categoryColors = getCategoryColors();
    
    new Chart(ctx, {
      type: 'doughnut',
      data: {
        labels: ['Present', 'Absent', 'Late', 'Excused'],
        datasets: [{
          data: [presentCount, absentCount, lateCount, excusedCount],
          backgroundColor: [
            categoryColors.present,
            categoryColors.absent,
            categoryColors.late,
            categoryColors.excused
          ],
          borderWidth: 1
        }]
      },
      options: {
        responsive: true,
        plugins: {
          legend: {
            position: 'right',
          },
          title: {
            display: true,
            text: 'Attendance Overview'
          }
        }
      }
    });
  }
  
  // Subject attendance chart (for teachers or admins)
  const subjectAttendanceElement = document.getElementById('subject-attendance-chart');
  if (subjectAttendanceElement) {
    try {
      const subjectsData = JSON.parse(subjectAttendanceElement.dataset.subjects || '{}');
      const subjectNames = Object.keys(subjectsData);
      
      if (subjectNames.length > 0) {
        const percentages = subjectNames.map(name => subjectsData[name].present_percentage || 0);
        const backgroundColors = subjectNames.map(() => {
          const r = Math.floor(Math.random() * 200);
          const g = Math.floor(Math.random() * 200);
          const b = Math.floor(Math.random() * 200);
          return `rgba(${r}, ${g}, ${b}, 0.7)`;
        });
        
        const ctx = subjectAttendanceElement.getContext('2d');
        
        new Chart(ctx, {
          type: 'bar',
          data: {
            labels: subjectNames,
            datasets: [{
              label: 'Attendance %',
              data: percentages,
              backgroundColor: backgroundColors,
              borderWidth: 1
            }]
          },
          options: {
            responsive: true,
            scales: {
              y: {
                beginAtZero: true,
                max: 100
              }
            },
            plugins: {
              legend: {
                display: false
              },
              title: {
                display: true,
                text: 'Attendance Percentage by Subject'
              }
            }
          }
        });
      }
    } catch (e) {
      console.error('Error parsing subject data for chart:', e);
    }
  }
  
  // Weekly attendance trend chart
  const weeklyTrendElement = document.getElementById('weekly-attendance-trend');
  if (weeklyTrendElement) {
    try {
      const weeklyData = JSON.parse(weeklyTrendElement.dataset.trend || '{}');
      const days = Object.keys(weeklyData);
      
      if (days.length > 0) {
        const presentCounts = days.map(day => weeklyData[day].present || 0);
        const absentCounts = days.map(day => weeklyData[day].absent || 0);
        const lateCounts = days.map(day => weeklyData[day].late || 0);
        
        const ctx = weeklyTrendElement.getContext('2d');
        const categoryColors = getCategoryColors();
        
        new Chart(ctx, {
          type: 'line',
          data: {
            labels: days,
            datasets: [
              {
                label: 'Present',
                data: presentCounts,
                borderColor: categoryColors.present,
                backgroundColor: 'transparent',
                tension: 0.1
              },
              {
                label: 'Absent',
                data: absentCounts,
                borderColor: categoryColors.absent,
                backgroundColor: 'transparent',
                tension: 0.1
              },
              {
                label: 'Late',
                data: lateCounts,
                borderColor: categoryColors.late,
                backgroundColor: 'transparent',
                tension: 0.1
              }
            ]
          },
          options: {
            responsive: true,
            scales: {
              y: {
                beginAtZero: true
              }
            },
            plugins: {
              title: {
                display: true,
                text: 'Weekly Attendance Trend'
              }
            }
          }
        });
      }
    } catch (e) {
      console.error('Error parsing weekly trend data for chart:', e);
    }
  }
}
