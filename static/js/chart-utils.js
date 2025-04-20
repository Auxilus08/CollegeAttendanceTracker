// Chart and data visualization utility functions

// Create a consistent color scheme for attendance statuses
const attendanceStatusColors = {
  present: '#28a745', // Green
  absent: '#dc3545',  // Red
  late: '#ffc107',    // Yellow
  excused: '#17a2b8'  // Cyan
};

// Function to create a default attendance summary chart
function createAttendanceSummaryChart(elementId, data) {
  const ctx = document.getElementById(elementId).getContext('2d');
  
  return new Chart(ctx, {
    type: 'doughnut',
    data: {
      labels: ['Present', 'Absent', 'Late', 'Excused'],
      datasets: [{
        data: [
          data.present || 0,
          data.absent || 0,
          data.late || 0,
          data.excused || 0
        ],
        backgroundColor: [
          attendanceStatusColors.present,
          attendanceStatusColors.absent,
          attendanceStatusColors.late,
          attendanceStatusColors.excused
        ],
        borderWidth: 1
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          position: 'right',
        },
        title: {
          display: true,
          text: 'Attendance Summary'
        },
        tooltip: {
          callbacks: {
            label: function(context) {
              const label = context.label || '';
              const value = context.raw || 0;
              const total = context.dataset.data.reduce((a, b) => a + b, 0);
              const percentage = Math.round((value / total) * 100);
              return `${label}: ${value} (${percentage}%)`;
            }
          }
        }
      }
    }
  });
}

// Function to create a bar chart for attendance by subject
function createSubjectAttendanceChart(elementId, data) {
  const ctx = document.getElementById(elementId).getContext('2d');
  
  // Extract subject names and attendance data
  const subjectNames = Object.keys(data);
  const presentData = subjectNames.map(subject => data[subject].present || 0);
  const absentData = subjectNames.map(subject => data[subject].absent || 0);
  const lateData = subjectNames.map(subject => data[subject].late || 0);
  const excusedData = subjectNames.map(subject => data[subject].excused || 0);
  
  return new Chart(ctx, {
    type: 'bar',
    data: {
      labels: subjectNames,
      datasets: [
        {
          label: 'Present',
          data: presentData,
          backgroundColor: attendanceStatusColors.present,
          stack: 'Stack 0',
        },
        {
          label: 'Absent',
          data: absentData,
          backgroundColor: attendanceStatusColors.absent,
          stack: 'Stack 0',
        },
        {
          label: 'Late',
          data: lateData,
          backgroundColor: attendanceStatusColors.late,
          stack: 'Stack 0',
        },
        {
          label: 'Excused',
          data: excusedData,
          backgroundColor: attendanceStatusColors.excused,
          stack: 'Stack 0',
        }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      scales: {
        x: {
          stacked: true,
        },
        y: {
          stacked: true,
          beginAtZero: true
        }
      },
      plugins: {
        legend: {
          position: 'top',
        },
        title: {
          display: true,
          text: 'Attendance by Subject'
        }
      }
    }
  });
}

// Function to create a line chart for attendance trends over time
function createAttendanceTrendChart(elementId, data) {
  const ctx = document.getElementById(elementId).getContext('2d');
  
  // Extract dates and attendance counts
  const dates = Object.keys(data).sort();
  const presentCounts = dates.map(date => data[date].present || 0);
  const absentCounts = dates.map(date => data[date].absent || 0);
  const lateCounts = dates.map(date => data[date].late || 0);
  const excusedCounts = dates.map(date => data[date].excused || 0);
  
  // Format dates for display
  const formattedDates = dates.map(date => {
    const d = new Date(date);
    return `${d.getDate()}/${d.getMonth() + 1}`;
  });
  
  return new Chart(ctx, {
    type: 'line',
    data: {
      labels: formattedDates,
      datasets: [
        {
          label: 'Present',
          data: presentCounts,
          borderColor: attendanceStatusColors.present,
          backgroundColor: 'transparent',
          tension: 0.4
        },
        {
          label: 'Absent',
          data: absentCounts,
          borderColor: attendanceStatusColors.absent,
          backgroundColor: 'transparent',
          tension: 0.4
        },
        {
          label: 'Late',
          data: lateCounts,
          borderColor: attendanceStatusColors.late,
          backgroundColor: 'transparent',
          tension: 0.4
        },
        {
          label: 'Excused',
          data: excusedCounts,
          borderColor: attendanceStatusColors.excused,
          backgroundColor: 'transparent',
          tension: 0.4
        }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      scales: {
        y: {
          beginAtZero: true
        }
      },
      plugins: {
        legend: {
          position: 'top',
        },
        title: {
          display: true,
          text: 'Attendance Trend Over Time'
        }
      }
    }
  });
}

// Function to create a horizontal bar chart for student attendance rates
function createStudentAttendanceChart(elementId, data) {
  const ctx = document.getElementById(elementId).getContext('2d');
  
  // Extract student names and attendance percentages
  const studentNames = Object.keys(data);
  const attendanceRates = studentNames.map(student => data[student].present_percentage || 0);
  
  // Generate background colors based on attendance rates
  const backgroundColors = attendanceRates.map(rate => {
    if (rate >= 90) return '#28a745';      // Green for excellent
    if (rate >= 75) return '#17a2b8';      // Cyan for good
    if (rate >= 60) return '#ffc107';      // Yellow for average
    return '#dc3545';                      // Red for poor
  });
  
  return new Chart(ctx, {
    type: 'bar',
    data: {
      labels: studentNames,
      datasets: [{
        axis: 'y',
        label: 'Attendance %',
        data: attendanceRates,
        backgroundColor: backgroundColors,
        borderWidth: 1
      }]
    },
    options: {
      indexAxis: 'y',
      responsive: true,
      maintainAspectRatio: false,
      scales: {
        x: {
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
          text: 'Student Attendance Rates'
        }
      }
    }
  });
}
