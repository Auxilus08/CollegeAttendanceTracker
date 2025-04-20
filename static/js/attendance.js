// Attendance management functionality

document.addEventListener('DOMContentLoaded', function() {
  // Handle subject selection for attendance marking
  const subjectSelect = document.getElementById('subject-select');
  if (subjectSelect) {
    subjectSelect.addEventListener('change', function() {
      // Find the form this select belongs to
      const form = this.closest('form');
      if (form) {
        form.submit();
      }
    });
  }
  
  // Handle slot selection for attendance marking
  const slotSelect = document.getElementById('slot-select');
  if (slotSelect) {
    slotSelect.addEventListener('change', function() {
      // Find the form this select belongs to
      const form = this.closest('form');
      if (form) {
        form.submit();
      }
    });
  }
  
  // Handle date selection for attendance marking
  const dateSelect = document.getElementById('attendance-date');
  if (dateSelect) {
    dateSelect.addEventListener('change', function() {
      // Find the form this select belongs to
      const form = this.closest('form');
      if (form) {
        form.submit();
      }
    });
  }
  
  // Mark all students as present button
  const markAllPresentBtn = document.getElementById('mark-all-present');
  if (markAllPresentBtn) {
    markAllPresentBtn.addEventListener('click', function() {
      const statusSelects = document.querySelectorAll('select[name="statuses"]');
      statusSelects.forEach(select => {
        select.value = 'present';
      });
    });
  }
  
  // Mark all students as absent button
  const markAllAbsentBtn = document.getElementById('mark-all-absent');
  if (markAllAbsentBtn) {
    markAllAbsentBtn.addEventListener('click', function() {
      const statusSelects = document.querySelectorAll('select[name="statuses"]');
      statusSelects.forEach(select => {
        select.value = 'absent';
      });
    });
  }
  
  // Reset all attendance statuses button
  const resetAllBtn = document.getElementById('reset-all-statuses');
  if (resetAllBtn) {
    resetAllBtn.addEventListener('click', function() {
      const statusSelects = document.querySelectorAll('select[name="statuses"]');
      statusSelects.forEach(select => {
        select.selectedIndex = 0;
      });
    });
  }
  
  // Attendance filter form submit handler
  const attendanceFilterForm = document.getElementById('attendance-filter-form');
  if (attendanceFilterForm) {
    attendanceFilterForm.addEventListener('submit', function(e) {
      // Remove empty parameters
      const formElements = this.elements;
      for (let i = 0; i < formElements.length; i++) {
        const element = formElements[i];
        if (element.type !== 'submit' && element.value === '') {
          element.disabled = true;
        }
      }
    });
  }
  
  // Initialize attendance summary chart if element exists
  const attendanceChartElement = document.getElementById('attendance-summary-chart');
  if (attendanceChartElement) {
    renderAttendanceSummaryChart(attendanceChartElement);
  }
  
  // Initialize subject-wise attendance chart if element exists
  const subjectAttendanceChartElement = document.getElementById('subject-attendance-chart');
  if (subjectAttendanceChartElement) {
    renderSubjectAttendanceChart(subjectAttendanceChartElement);
  }
});

// Render overall attendance summary chart
function renderAttendanceSummaryChart(chartElement) {
  try {
    // Create a data object from the individual data attributes
    const chartData = {
      present: parseInt(chartElement.getAttribute('data-present') || 0),
      absent: parseInt(chartElement.getAttribute('data-absent') || 0),
      late: parseInt(chartElement.getAttribute('data-late') || 0),
      excused: parseInt(chartElement.getAttribute('data-excused') || 0)
    };
    
    // Create the chart
    const ctx = chartElement.getContext('2d');
    const categoryColors = getCategoryColors();
    
    new Chart(ctx, {
      type: 'doughnut',
      data: {
        labels: ['Present', 'Absent', 'Late', 'Excused'],
        datasets: [{
          data: [
            chartData.present || 0,
            chartData.absent || 0, 
            chartData.late || 0,
            chartData.excused || 0
          ],
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
            text: 'Attendance Summary'
          }
        }
      }
    });
  } catch (e) {
    console.error('Error rendering attendance chart:', e);
    chartElement.innerHTML = 'Error loading chart data';
  }
}

// Render subject-wise attendance chart
function renderSubjectAttendanceChart(chartElement) {
  // Get data from the data attribute
  const chartDataStr = chartElement.getAttribute('data-stats') || chartElement.getAttribute('data-subjects');
  if (!chartDataStr) {
    console.warn('No data found for subject attendance chart');
    return;
  }
  
  try {
    const subjectStats = JSON.parse(chartDataStr);
    const subjectNames = Object.keys(subjectStats);
    
    if (subjectNames.length === 0) {
      console.warn('No subjects found in the data');
      return;
    }
    
    const presentData = [];
    const absentData = [];
    const lateData = [];
    const excusedData = [];
    
    subjectNames.forEach(subject => {
      const stats = subjectStats[subject];
      presentData.push(stats.present || 0);
      absentData.push(stats.absent || 0);
      lateData.push(stats.late || 0);
      excusedData.push(stats.excused || 0);
    });
    
    // Create the chart
    const ctx = chartElement.getContext('2d');
    const categoryColors = getCategoryColors();
    
    new Chart(ctx, {
      type: 'bar',
      data: {
        labels: subjectNames,
        datasets: [
          {
            label: 'Present',
            data: presentData,
            backgroundColor: categoryColors.present,
            borderWidth: 1
          },
          {
            label: 'Absent',
            data: absentData,
            backgroundColor: categoryColors.absent,
            borderWidth: 1
          },
          {
            label: 'Late',
            data: lateData,
            backgroundColor: categoryColors.late,
            borderWidth: 1
          },
          {
            label: 'Excused',
            data: excusedData,
            backgroundColor: categoryColors.excused,
            borderWidth: 1
          }
        ]
      },
      options: {
        responsive: true,
        scales: {
          x: {
            stacked: true,
          },
          y: {
            stacked: true
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
  } catch (e) {
    console.error('Error rendering subject attendance chart:', e);
    chartElement.innerHTML = 'Error loading chart data';
  }
}
