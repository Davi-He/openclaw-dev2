let countdownInterval = null;
let targetDate = null;

document.addEventListener('DOMContentLoaded', function() {
    const targetDateInput = document.getElementById('target-date');
    const targetTimeInput = document.getElementById('target-time');
    const setCountdownBtn = document.getElementById('set-countdown');
    const resetCountdownBtn = document.getElementById('reset-countdown');
    const eventNameInput = document.getElementById('event-name');
    const eventTitleDiv = document.getElementById('event-title');
    const daysSpan = document.getElementById('days');
    const hoursSpan = document.getElementById('hours');
    const minutesSpan = document.getElementById('minutes');
    const secondsSpan = document.getElementById('seconds');

    // 设置默认时间为明天
    const tomorrow = new Date();
    tomorrow.setDate(tomorrow.getDate() + 1);
    targetDateInput.value = formatDate(tomorrow);
    targetTimeInput.value = '00:00';

    setCountdownBtn.addEventListener('click', function() {
        const dateValue = targetDateInput.value;
        const timeValue = targetTimeInput.value;
        const eventName = eventNameInput.value || '特殊时刻';

        if (!dateValue || !timeValue) {
            alert('请设置目标日期和时间');
            return;
        }

        // 合并日期和时间
        const dateTimeString = `${dateValue}T${timeValue}`;
        targetDate = new Date(dateTimeString);

        // 检查是否为有效日期
        if (isNaN(targetDate.getTime())) {
            alert('无效的日期或时间');
            return;
        }

        // 如果目标时间已过，则设置为明天同一时间
        if (targetDate <= new Date()) {
            alert('目标时间必须是未来的某个时间');
            return;
        }

        eventTitleDiv.textContent = `距离 ${eventName} 还有:`; 

        // 开始倒计时
        startCountdown();

        // 保存设置到本地存储
        saveSettings(dateValue, timeValue, eventName);
    });

    resetCountdownBtn.addEventListener('click', function() {
        if (countdownInterval) {
            clearInterval(countdownInterval);
            countdownInterval = null;
        }
        
        // 清空显示
        daysSpan.textContent = '00';
        hoursSpan.textContent = '00';
        minutesSpan.textContent = '00';
        secondsSpan.textContent = '00';
        
        eventTitleDiv.textContent = '';
        
        // 重置输入框为默认值
        const tomorrow = new Date();
        tomorrow.setDate(tomorrow.getDate() + 1);
        targetDateInput.value = formatDate(tomorrow);
        targetTimeInput.value = '00:00';
        eventNameInput.value = '';
    });

    // 尝试从本地存储加载之前的设置
    loadSavedSettings();

    // 如果已有设置，则自动开始倒计时
    function loadSavedSettings() {
        const savedDate = localStorage.getItem('countdown_date');
        const savedTime = localStorage.getItem('countdown_time');
        const savedEvent = localStorage.getItem('countdown_event');

        if (savedDate && savedTime) {
            targetDateInput.value = savedDate;
            targetTimeInput.value = savedTime;
            eventNameInput.value = savedEvent || '';

            // 自动启动倒计时
            const dateTimeString = `${savedDate}T${savedTime}`;
            targetDate = new Date(dateTimeString);

            if (targetDate > new Date()) {
                eventTitleDiv.textContent = `距离 ${savedEvent || '特殊时刻'} 还有:`;
                startCountdown();
            } else {
                // 如果保存的时间已过期，则清除存储
                localStorage.removeItem('countdown_date');
                localStorage.removeItem('countdown_time');
                localStorage.removeItem('countdown_event');
            }
        }
    }

    function saveSettings(date, time, event) {
        localStorage.setItem('countdown_date', date);
        localStorage.setItem('countdown_time', time);
        localStorage.setItem('countdown_event', event);
    }

    function startCountdown() {
        if (countdownInterval) {
            clearInterval(countdownInterval);
        }

        updateCountdown(); // 立即更新一次
        countdownInterval = setInterval(updateCountdown, 1000);
    }

    function updateCountdown() {
        if (!targetDate) return;

        const now = new Date();
        const difference = targetDate - now;

        if (difference <= 0) {
            clearInterval(countdownInterval);
            daysSpan.textContent = '00';
            hoursSpan.textContent = '00';
            minutesSpan.textContent = '00';
            secondsSpan.textContent = '00';
            eventTitleDiv.textContent = '时间到了！';
            return;
        }

        const days = Math.floor(difference / (1000 * 60 * 60 * 24));
        const hours = Math.floor((difference % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
        const minutes = Math.floor((difference % (1000 * 60 * 60)) / (1000 * 60));
        const seconds = Math.floor((difference % (1000 * 60)) / 1000);

        daysSpan.textContent = String(days).padStart(2, '0');
        hoursSpan.textContent = String(hours).padStart(2, '0');
        minutesSpan.textContent = String(minutes).padStart(2, '0');
        secondsSpan.textContent = String(seconds).padStart(2, '0');
    }

    function formatDate(date) {
        const year = date.getFullYear();
        const month = String(date.getMonth() + 1).padStart(2, '0');
        const day = String(date.getDate()).padStart(2, '0');
        return `${year}-${month}-${day}`;
    }
});