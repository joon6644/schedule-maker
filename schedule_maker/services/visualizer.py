"""
HTML 시각화 모듈
시간표 조합을 인터랙티브 HTML로 출력
"""
from typing import List
from ..core.models import Schedule
import json
import random


class HtmlVisualizer:
    """HTML 시각화 생성기"""

    HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>시간표 조합 결과</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 20px;
            height: 100vh; /* 화면 꽉 채우기 */
            overflow: hidden; /* 페이지 스크롤 제거 */
        }
        
        .container {
            max-width: 1400px;
            margin: 0 auto;
            background: white;
            border-radius: 16px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            display: flex;
            flex-direction: column;
            height: 100%; /* 부모(body) 높이 상속 */
        }
        
        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            text-align: center;
        }
        
        .header h1 {
            font-size: 2.5em;
            margin-bottom: 10px;
        }
        
        .controls {
            background: #f8f9fa;
            padding: 20px 30px;
            display: flex;
            align-items: center;
            justify-content: space-between;
            border-bottom: 2px solid #e9ecef;
        }
        
        .nav-buttons {
            display: flex;
            gap: 10px;
        }
        
        .btn {
            padding: 12px 24px;
            font-size: 16px;
            border: none;
            border-radius: 8px;
            cursor: pointer;
            transition: all 0.3s;
            font-weight: 600;
        }
        
        .btn-primary {
            background: #667eea;
            color: white;
        }
        
        .btn-primary:hover {
            background: #5568d3;
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
        }
        
        .btn:disabled {
            opacity: 0.5;
            cursor: not-allowed;
        }
        
        .counter {
            font-size: 1.3em;
            font-weight: bold;
            color: #495057;
        }
        
        .content {
            display: flex;
            padding: 20px 30px 30px 30px; /* 하단 패딩 확보 */
            gap: 30px;
            flex: 1; /* 남은 공간 모두 차지 */
            overflow: hidden; /* 내부 스크롤을 위해 숨김 */
            height: 100%;
        }
        
        .sidebar {
            flex: 0 0 300px;
            display: flex;
            flex-direction: column;
            gap: 20px;
            height: 100%;
            overflow: hidden; /* 사이드바 내부 스크롤 허용 */
        }
        
        .info-box {
            background: #f8f9fa;
            padding: 20px;
            border-radius: 12px;
            flex-shrink: 0; /* 크기 줄어들지 않음 */
        }
        
        .info-box.course-list-box {
            flex: 1; /* 남은 높이 차지 */
            display: flex;
            flex-direction: column;
            min-height: 0; /* flex 자식의 스크롤을 위해 필수 */
            overflow: hidden;
            margin-bottom: 0;
        }
        
        .info-box h3 {
            color: #495057;
            margin-bottom: 15px;
            font-size: 1.2em;
            flex-shrink: 0;
        }

        .course-list {
            list-style: none;
            display: flex;
            flex-direction: column;
            overflow-y: auto; /* 상자 안에서 스크롤 */
            padding-right: 5px;
            flex: 1; /* 부모 높이 채움 */
        }
        
        /* 스크롤바 스타일링 */
        .course-list::-webkit-scrollbar {
            width: 8px;
        }
        .course-list::-webkit-scrollbar-track {
            background: #f1f1f1; 
            border-radius: 4px;
        }
        .course-list::-webkit-scrollbar-thumb {
            background: #cbd5e0; 
            border-radius: 4px;
        }
        .course-list::-webkit-scrollbar-thumb:hover {
            background: #a0aec0; 
        }
        
        .course-item {
            padding: 12px;
            margin: 8px 0;
            border-radius: 8px;
            background: white;
            border-left: 4px solid;
            transition: all 0.2s;
            cursor: pointer;
        }
        
        .course-item:hover {
            transform: translateX(4px);
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            background: #eef2ff;
            cursor: pointer;
        }
        
        .course-name {
            font-weight: bold;
            margin-bottom: 4px;
        }
        
        .course-detail {
            font-size: 0.9em;
            font-size: 0.9em;
            color: #6c757d;
        }

        .course-item.inactive {
            border-left-color: #dee2e6 !important;
            background: #f8f9fa;
            color: #adb5bd;
            opacity: 0.8;
            order: 1000; /* 일반 비활성 강의는 가장 아래 */
        }
        
        .course-item.inactive .course-name {
            color: #adb5bd;
        }
        
        .course-item.required {
            order: -1000 !important; /* 필수 강의 최상단 고정 */
            background-color: #fff1f2; /* 연한 빨강 배경으로 강조 */
        }

        .course-item.active {
            order: 0; /* 활성 강의는 상단 */
        }
        
        .course-item.stay-top {
            order: 500 !important; /* 방금 클릭한 비활성 강의는 비활성 중 가장 위 */
        }
        
        .course-item.pinned {
            /* order는 JS에서 동적으로 설정됨 */
            border: 2px solid #667eea !important;
            border-left: 4px solid #667eea !important;
            box-shadow: 0 0 8px rgba(102, 126, 234, 0.4);
            background: linear-gradient(135deg, #eef2ff 0%, #e0e7ff 100%) !important;
        }
        
        .unpin-btn {
            position: absolute;
            top: 4px;
            right: 4px;
            width: 20px;
            height: 20px;
            border: none;
            border-radius: 50%;
            background: #ef4444;
            color: white;
            font-size: 12px;
            font-weight: bold;
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
            opacity: 0.7;
            transition: all 0.2s;
        }
        
        .unpin-btn:hover {
            opacity: 1;
            transform: scale(1.1);
            box-shadow: 0 2px 6px rgba(239, 68, 68, 0.4);
        }
        
        .course-item.pinned {
            position: relative; /* unpin 버튼 위치 기준 */
        }
        
        .schedule-container {
            flex: 1;
            position: relative;
            overflow-y: auto; /* 시간표가 길면 여기서 스크롤 */
            background: #dee2e6; /* 스크롤 시 배경 */
            border-radius: 12px;
        }
        
        .schedule-table {
            display: grid;
            grid-template-columns: 60px repeat(5, 1fr);
            grid-template-rows: 40px repeat(13, 60px);  /* 헤더 40px + 13시간 (9:00-22:00) */
            gap: 1px;
            background: #dee2e6;
            border-radius: 12px;
            overflow: hidden;
        }
        
        .time-cell, .day-header, .day-column {
            background: white;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 0.85em;
        }
        
        .day-header {
            font-weight: bold;
            background: #667eea;
            color: white;
            font-size: 1em;
        }
        
        .time-cell {
            font-weight: 600;
            color: #6c757d;
            font-size: 0.8em;
        }
        
        .day-column {
            background: #f8f9fa;
            position: relative;  /* 강의 블럭의 부모 */
            padding: 0;
        }
        
        .course-block {
            position: absolute;
            left: 2px;
            right: 2px;
            border-radius: 4px;
            padding: 8px 4px;
            font-weight: 600;
            color: white;
            text-align: center;
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            transition: all 0.2s;
            z-index: 5;
        }
        
        .course-block:hover {
            transform: scale(1.02);
            box-shadow: 0 4px 12px rgba(0,0,0,0.2);
            z-index: 10;
        }
        
        .empty-message {
            grid-column: 1 / -1;
            padding: 60px;
            text-align: center;
            color: #6c757d;
            font-size: 1.2em;
        }

        /* Toast Notification Styles */
        .toast-container {
            position: fixed;
            top: 20px;
            right: 20px;
            z-index: 10000;
            display: flex;
            flex-direction: column;
            pointer-events: none;
            padding-bottom: 20px; /* Space for hover expansion */
        }

        .toast {
            background: white;
            border-left: 6px solid #0078d4;
            padding: 16px 20px;
            border-radius: 12px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.15);
            font-family: 'Segoe UI', sans-serif;
            min-width: 320px;
            max-width: 400px;
            display: flex;
            flex-direction: column;
            gap: 6px;
            
            /* Initial State */
            opacity: 0;
            transform: translateX(30px);
            animation: slideIn 0.3s cubic-bezier(0.2, 0.8, 0.2, 1) forwards;
            
            pointer-events: auto;
            cursor: pointer;
            transition: all 0.3s cubic-bezier(0.25, 0.8, 0.25, 1);
            margin-bottom: 15px; /* Base spacing */
            position: relative;
        }

        /* Stacking: Making them pile up nicely */
        .toast:not(:first-child) {
            margin-top: -90px; /* Aggressive overlap: hide most of previous toast */
            transform: scale(0.95) translateY(10px);
            opacity: 0.5;
            z-index: -1;
            filter: blur(0.5px); /* Soften background items */
        }
        
        .toast:nth-child(3) {
             transform: scale(0.9) translateY(20px);
             opacity: 0.3;
             z-index: -2;
        }

        /* Hover: Expand the stack to see details */
        .toast-container:hover .toast {
            margin-top: 10px !important;
            transform: scale(1) translateY(0) !important;
            opacity: 1 !important;
            z-index: auto !important;
            filter: none !important;
        }

        /* Hiding Animation - Transition Based (Robust) */
        .toast.hiding {
            animation: none !important; /* Kill slideIn lock */
            opacity: 0 !important;
            transform: translateY(-50px) scale(0.9) !important; /* Move up more */
            margin-top: -100px !important; /* Collapse space */
            pointer-events: none !important;
        }
        
        @keyframes slideIn {
            from { opacity: 0; transform: translateX(30px); }
            to { opacity: 1; transform: translateX(0); }
        }

        .toast.error {
            border-left-color: #ef4444; /* Red for error */
        }
        
        .toast.success {
            border-left-color: #10b981; /* Green for success */
        }

        .toast-title {
            font-weight: bold;
            font-size: 1.05em;
            color: #1f2937;
        }

        .toast-message {
            font-size: 0.9em;
            color: #4b5563;
            line-height: 1.4;
        }

        @keyframes slideIn {
            from { opacity: 0; transform: translateX(50px); }
            to { opacity: 1; transform: translateX(0); }
        }
        
        @keyframes fadeOut {
            to { opacity: 0; transform: translateY(-20px); } /* Fade Up */
        }
    </style>
</head>
<body>
    <div id="toast-container" class="toast-container"></div>
    <div class="container">
        <!-- Header removed by user request -->

        
        <div class="controls">
            <div class="nav-buttons">
                <button class="btn btn-primary" onclick="prevSchedule()" id="prevBtn">
                    ◀ 이전
                </button>
                <button class="btn btn-primary" onclick="nextSchedule()" id="nextBtn">
                    다음 ▶
                </button>
            </div>
            <div class="counter">
                <span id="current">1</span> / <span id="total">0</span>
            </div>
        </div>
        
        <div class="content">
            <div class="sidebar">
                <div class="info-box">
                    <h3>📊 조합 정보</h3>
                    <div class="info-item">
                        <span>총 학점</span>
                        <strong id="credits">0</strong>
                    </div>
                    <div class="info-item">
                        <span>강의 수</span>
                        <strong id="courseCount">0</strong>
                    </div>
                </div>
                
                <div class="info-box course-list-box">
                    <h3>📚 강의 목록</h3>
                    <ul class="course-list" id="courseList"></ul>
                </div>
            </div>
            
            <div class="schedule-container">
                <div class="schedule-table" id="schedule-table"></div>
            </div>
        </div>
    </div>
    
    <script>
        // 데이터
        const schedules = SCHEDULE_DATA_PLACEHOLDER;
        const allCourseNames = ALL_COURSES_PLACEHOLDER; // 전체 강의 목록 (필수 + 희망)
        const requiredCourseNames = REQUIRED_COURSES_PLACEHOLDER; // 필수 강의 목록
        
        let currentIndex = 0;
        let lastInteractedCourse = null; // 마지막으로 클릭한 강의 (정렬 유지용)
        let courseFilters = new Map(); // 다중 강의 필터: 강의명 -> 시간대 (AND 조건)
        let filteredIndices = []; // 필터된 스케줄 인덱스 배열
        let filteredPosition = -1; // 필터 내 현재 위치
        
        // 요일 및 시간 설정
        const WEEKDAYS = ['월', '화', '수', '목', '금'];
        // 토요반이 있는 시간표만 토요일 열을 보여줌 (initTimetable 에서 갱신)
        let days = WEEKDAYS;
        const startHour = 9;
        const endHour = 22;  // 22:00까지 표시 (야간 수업 대응)
        const slotsPerHour = 2; // 30분 단위

        // Toast Notification Function
        function showToast(title, message, type='info') {
            const container = document.getElementById('toast-container');
            
            const toast = document.createElement('div');
            toast.className = `toast ${type}`;
            
            const titleEl = document.createElement('div');
            titleEl.className = 'toast-title';
            titleEl.textContent = title;
            
            const msgEl = document.createElement('div');
            msgEl.className = 'toast-message';
            msgEl.textContent = message;
            
            toast.appendChild(titleEl);
            toast.appendChild(msgEl);
            
            toast.onclick = () => {
                toast.classList.add('hiding');
                setTimeout(() => toast.remove(), 300);
            };

            // Prepend (Newest on Top)
            if (container.firstChild) {
                container.insertBefore(toast, container.firstChild);
            } else {
                container.appendChild(toast);
            }
            
            // Limit to max 3 visible toasts (Keep stack clean)
            while (container.children.length > 3) {
                container.lastChild.remove();
            }
            
            // Auto disappear
            setTimeout(() => {
                // Check if still in DOM
                if (toast.parentElement) {
                    toast.classList.add('hiding');
                    // Force removal after animation
                    setTimeout(() => {
                         if (toast.parentElement) toast.remove();
                    }, 300);
                }
            }, 4000);
        }
        
        // HSL 색상 생성 (강의별 고유 색상)
        const courseColors = new Map();
        let colorIndex = 0;
        
        function getCourseColor(courseName) {
            if (!courseColors.has(courseName)) {
                const hue = (colorIndex * 137.5) % 360; // 황금각으로 분산
                courseColors.set(courseName, `hsl(${hue}, 70%, 60%)`);
                colorIndex++;
            }
            return courseColors.get(courseName);
        }
        
        // 시간표 그리드 초기화
        function initTimetable(schedule) {
            const table = document.getElementById('schedule-table');
            table.innerHTML = '';
            const hasSat = !!schedule && schedule.courses.some(c => c.time_slots.some(s => s.day === '토'));
            days = hasSat ? [...WEEKDAYS, '토'] : WEEKDAYS;
            table.style.gridTemplateColumns = `60px repeat(${days.length}, 1fr)`;
            
            // 빈 좌상단 셀
            table.innerHTML += '<div class="day-header"></div>';
            
            // 요일 헤더
            days.forEach(day => {
                const cell = document.createElement('div');
                cell.className = 'day-header';
                cell.textContent = day;
                table.appendChild(cell);
            });
            
            // 시간 및 요일 컴럼 (1시간 단위)
            for (let hour = startHour; hour < endHour; hour++) {
                const timeStr = `${hour.toString().padStart(2, '0')}:00`;
                
                const timeCell = document.createElement('div');
                timeCell.className = 'time-cell';
                timeCell.textContent = timeStr;
                table.appendChild(timeCell);
                
                // 각 요일별 컴럼 (강의 블럭의 container)
                for (let d = 0; d < days.length; d++) {
                    const dayCol = document.createElement('div');
                    dayCol.className = 'day-column';
                    dayCol.id = `day-col-${d}-${hour}`;
                    table.appendChild(dayCol);
                }
            }
        }
        
        // 시간을 슬롯 인덱스로 변환
        function timeToSlot(timeStr) {
            const [hour, minute] = timeStr.split(':').map(Number);
            return ((hour - startHour) * slotsPerHour) + (minute / 30);
        }
        
        // 시간표 렌더링
        function renderSchedule(index) {
            if (index < 0 || index >= schedules.length) return;
            
            currentIndex = index;
            const schedule = schedules[index];
            
            // 컨트롤 업데이트
            if (filteredIndices.length > 0 && filteredPosition >= 0) {
                // 필터 모드: 필터된 스케줄 내 위치 표시
                document.getElementById('current').textContent = `${filteredPosition + 1}`;
                const filterCount = courseFilters.size;
                document.getElementById('total').textContent = `${filteredIndices.length} (${filterCount}개 고정)`;
            } else {
                // 일반 모드
                document.getElementById('current').textContent = index + 1;
                document.getElementById('total').textContent = schedules.length;
            }
            document.getElementById('credits').textContent = schedule.total_credits + '학점';
            document.getElementById('courseCount').textContent = schedule.courses.length + '개';
            
            // Random Fill 알림 (최초 1회만 표시)
            if (schedule.has_random_filled && !window.hasShownRandomFillToast) {
                showToast(
                    "🎲 무작위 채우기 발동",
                    "선택한 강의만으로는 최소 학점을 채울 수 없어, 공강 시간에 '전학년' 대상 강의가 자동으로 추가되었습니다.",
                    "success"
                );
                window.hasShownRandomFillToast = true;
            }
            
            // 버튼 상태 - 순환 네비게이션이므로 항상 활성화
            document.getElementById('prevBtn').disabled = false;
            document.getElementById('nextBtn').disabled = false;
            
            // 강의 목록
            // 강의 목록
            const courseList = document.getElementById('courseList');
            courseList.innerHTML = '';
            
            // 1. 현재 시간표에 있는 강의들 (활성) - Set으로 미리 파악
            const activeCourses = new Set();
            schedule.courses.forEach(course => {
                activeCourses.add(course.name);
            });
            
            // 2. 전체 강의 목록 순회 (단일 루프)
            allCourseNames.forEach(courseName => {
                let courseData = null;
                let isActive = false;
                
                if (activeCourses.has(courseName)) {
                    // 활성 강의
                    courseData = schedule.courses.find(c => c.name === courseName);
                    isActive = true;
                } else {
                    // 비활성 강의
                    courseData = findCourseInfo(courseName);
                    isActive = false;
                }
                
                if (courseData) {
                    createCourseItem(courseData, isActive);
                }
            });
            
            // 강의 아이템 생성 헬퍼 함수
            function createCourseItem(course, isActive) {
                const li = document.createElement('li');
                
                // 필수 여부 및 핀 여부 확인
                const isRequired = requiredCourseNames.includes(course.name);
                const isPinned = courseFilters.has(course.name);
                
                // 핀된 강의는 active/inactive 대신 pinned 클래스만 적용 (고정 위치)
                if (isPinned && !isRequired) {
                    li.className = 'course-item pinned';
                    li.style.borderLeftColor = getCourseColor(course.name);
                    // 핀 순서에 따라 order 값 지정 (-500, -499, -498...)
                    const pinnedKeys = Array.from(courseFilters.keys());
                    const pinnedOrder = pinnedKeys.indexOf(course.name);
                    li.style.order = -500 + pinnedOrder; // -500, -499, -498...
                } else if (!isRequired) {
                    li.className = `course-item ${isActive ? 'active' : 'inactive'}`;
                    if (isActive) {
                        li.style.borderLeftColor = getCourseColor(course.name);
                    } else {
                        // 비활성 상태라도 방금 상호작용한 강의면 상단 유지
                        if (course.name === lastInteractedCourse) {
                            li.classList.add('stay-top');
                        }
                    }
                } else {
                    // 필수 강의
                    li.className = `course-item ${isActive ? 'active' : 'inactive'}`;
                    if (isActive) {
                        li.style.borderLeftColor = getCourseColor(course.name);
                    }
                }
                
                // 필수 여부 확인 및 클래스 추가
                if (isRequired) {
                    li.classList.add('required');
                }
                
                // 핀된 강의에 pinned 클래스 추가 (필수 과목 포함)
                if (isPinned) {
                    li.classList.add('pinned');
                }
                
                // 데이터 속성 추가
                li.dataset.name = course.name;
                li.dataset.required = isRequired;
                if (isActive && course.time_slots.length > 0) {
                    li.dataset.time = `${course.time_slots[0].day} ${course.time_slots[0].start_time}`;
                } else {
                    li.dataset.time = 'NONE'; // 선택되지 않음
                }
                
                // 클릭 이벤트 연결
                li.onclick = function() { findAlternativeSchedule(this); };
                
                // 강의 정보 HTML
                let courseHtml = `
                    <div class="course-name">${course.name}${isRequired ? ' <span style="font-size:0.8em; color:#ef4444;">(필수)</span>' : ''}${isPinned ? ' <span style="font-size:0.8em;">📌</span>' : ''}</div>
                    <div class="course-detail">${course.professor} · ${course.credits}학점</div>
                `;
                
                // 핀된 강의에 해제 버튼 추가
                if (isPinned) {
                    courseHtml += `<button class="unpin-btn" onclick="unpinCourse(event, '${course.name}')" title="고정 해제">✕</button>`;
                }
                
                li.innerHTML = courseHtml;
                courseList.appendChild(li);
            }
            
            // 강의 정보 찾기 (전체 스케줄 탐색)
            function findCourseInfo(name) {
                for (let s of schedules) {
                    const found = s.courses.find(c => c.name === name);
                    if (found) return found;
                }
                return { name: name, professor: '-', credits: '-' };
            }
            
            // 시간표 그리드 초기화
            initTimetable(schedule);
            
            // 강의 블록 배치 (픽셀 기반 absolute positioning)
            schedule.courses.forEach(course => {
                course.time_slots.forEach(slot => {
                    const dayIndex = days.indexOf(slot.day);
                    if (dayIndex === -1) return;
                    
                    // 시간 파싱
                    const [startHour, startMin] = slot.start_time.split(':').map(Number);
                    const [endHour, endMin] = slot.end_time.split(':').map(Number);
                    
                    // 9시 기준 분 단위 계산
                    const startTotalMin = (startHour - 9) * 60 + startMin;
                    const endTotalMin = (endHour - 9) * 60 + endMin;
                    
                    // 픽셀 계산 (1시간 = 60px, 1분 = 1px)
                    const pixelsPerMinute = 60 / 60;  // 60px / 60분 = 1px/분
                    const topPx = startTotalMin * pixelsPerMinute;
                    const heightPx = (endTotalMin - startTotalMin) * pixelsPerMinute;
                    
                    // 시작 시간의 요일 컴럼 찾기
                    const startHourFor9AM = Math.floor(startTotalMin / 60) + 9;
                    const parentCol = document.getElementById(`day-col-${dayIndex}-${startHourFor9AM}`);
                    
                    if (!parentCol) {
                        console.log(`Could not find parent for ${course.name} at ${slot.day} ${slot.start_time}`);
                        return;
                    }
                    
                    // 해당 시간 셀 내에서의 오프셋 계산
                    const offsetInHour = startMin * pixelsPerMinute;
                    
                    // 블록 생성
                    const block = document.createElement('div');
                    block.className = 'course-block';
                    block.style.top = `${offsetInHour}px`;
                    block.style.height = `${heightPx}px`;
                    block.style.background = getCourseColor(course.name);
                    block.textContent = course.name;
                    block.title = `${course.name}\n${course.professor}\n${slot.day} ${slot.start_time}~${slot.end_time}`;
                    
                    parentCol.appendChild(block);
                });
            });
        }
        
        // 네비게이션 (순환 - deque.rotate 방식)
        function prevSchedule() {
            // 필터 모드일 때: 필터된 스케줄 내에서 순환
            if (filteredIndices.length > 0 && filteredPosition >= 0) {
                filteredPosition--;
                if (filteredPosition < 0) {
                    filteredPosition = filteredIndices.length - 1; // 처음에서 끝으로
                }
                renderSchedule(filteredIndices[filteredPosition]);
                return;
            }
            // 일반 모드: 순환
            lastInteractedCourse = null;
            let newIndex = currentIndex - 1;
            if (newIndex < 0) {
                newIndex = schedules.length - 1; // 처음에서 끝으로
            }
            renderSchedule(newIndex);
        }
        
        function nextSchedule() {
            // 필터 모드일 때: 필터된 스케줄 내에서 순환
            if (filteredIndices.length > 0 && filteredPosition >= 0) {
                filteredPosition++;
                if (filteredPosition >= filteredIndices.length) {
                    filteredPosition = 0; // 끝에서 처음으로
                }
                renderSchedule(filteredIndices[filteredPosition]);
                return;
            }
            // 일반 모드: 순환
            lastInteractedCourse = null;
            let newIndex = currentIndex + 1;
            if (newIndex >= schedules.length) {
                newIndex = 0; // 끝에서 처음으로
            }
            renderSchedule(newIndex);
        }
        
        // 키보드 단축키
        document.addEventListener('keydown', (e) => {
            if (e.key === 'ArrowLeft') prevSchedule();
            if (e.key === 'ArrowRight') nextSchedule();
            if (e.key === 'Escape') {
                // 필터 모드 해제 (모든 필터 초기화)
                if (filteredIndices.length > 0 || courseFilters.size > 0) {
                    courseFilters.clear();
                    filteredIndices = [];
                    filteredPosition = -1;
                    lastInteractedCourse = null;
                    renderSchedule(currentIndex); // 현재 위치 유지하며 다시 렌더링
                    console.log('All filters cleared');
                }
            }
        });
        
        // 특정 강의 핀 해제
        function unpinCourse(event, courseName) {
            event.stopPropagation(); // 부모 클릭 이벤트 방지
            
            if (!courseFilters.has(courseName)) return;
            
            courseFilters.delete(courseName);
            console.log(`Unpinned: ${courseName}`);
            
            // 남은 필터로 재계산
            if (courseFilters.size > 0) {
                // 남은 필터 조건으로 스케줄 재검색
                const newFilteredIndices = [];
                for (let i = 0; i < schedules.length; i++) {
                    const s = schedules[i];
                    let matchesAll = true;
                    
                    for (const [filterName, filterTime] of courseFilters) {
                        const c = s.courses.find(course => course.name === filterName);
                        let state = 'NONE';
                        if (c) {
                            state = `${c.time_slots[0].day} ${c.time_slots[0].start_time}`;
                        }
                        if (state !== filterTime) {
                            matchesAll = false;
                            break;
                        }
                    }
                    
                    if (matchesAll) {
                        newFilteredIndices.push(i);
                    }
                }
                
                filteredIndices = newFilteredIndices;
                filteredPosition = 0;
                
                if (filteredIndices.length > 0) {
                    renderSchedule(filteredIndices[0]);
                }
            } else {
                // 필터 없음
                filteredIndices = [];
                filteredPosition = -1;
                renderSchedule(currentIndex);
            }
        }
        
        // 대체 시간대 찾기 (인터랙티브 기능 - 다중 필터 AND 지원)
        function findAlternativeSchedule(element) {
            const courseName = element.dataset.name;
            lastInteractedCourse = courseName; // 상호작용 기록 (정렬 유지)
            
            const isRequired = element.dataset.required === 'true';
            const currentTime = element.dataset.time; // 'NONE' or '월 10:00'
            
            // 이미 핀된 강의인지 확인
            const isAlreadyPinned = courseFilters.has(courseName);
            
            // 새로운 강의 클릭: 현재 시간대로 핀만 (순환 안함)
            if (!isAlreadyPinned) {
                let targetTime = currentTime;

                // 현재 스케줄에 없는 강의(NONE)인 경우, 가능한 시간대 중 하나를 찾음
                if (targetTime === 'NONE') {
                     let potentialIndices = filteredIndices.length > 0 ? filteredIndices : 
                        Array.from({length: schedules.length}, (_, i) => i);
                     
                     for (const i of potentialIndices) {
                        const s = schedules[i];
                        const c = s.courses.find(course => course.name === courseName);
                        if (c) {
                            targetTime = `${c.time_slots[0].day} ${c.time_slots[0].start_time}`;
                            break; // 첫 번째 발견된 시간대 사용
                        }
                     }

                     if (targetTime === 'NONE') {
                         showToast(
                             "유일한 시간대입니다.",
                             "현재 설정된 조건(필수/고정 강의)과 충돌 없이 이동 가능한 다른 분반이 없습니다.",
                             "error"
                         );
                         console.log(`Cannot pin ${courseName}: no available schedule in current filter`);
                         return;
                     }
                }
                
                // 현재 시간대(혹은 찾은 시간대)로 핀
                courseFilters.set(courseName, targetTime);
                console.log(`Pinned ${courseName} at ${targetTime}`);
                
                // 현재 필터된 범위 내에서 이 시간대의 스케줄만 필터링
                let searchIndices = filteredIndices.length > 0 ? filteredIndices : 
                    Array.from({length: schedules.length}, (_, i) => i);
                
                const newFilteredIndices = [];
                for (const i of searchIndices) {
                    const s = schedules[i];
                    const c = s.courses.find(course => course.name === courseName);
                    if (c) {
                        const timeKey = `${c.time_slots[0].day} ${c.time_slots[0].start_time}`;
                        if (timeKey === targetTime) {
                            newFilteredIndices.push(i);
                        }
                    }
                }
                
                filteredIndices = newFilteredIndices;
                filteredPosition = 0;
                
                if (filteredIndices.length === 0) {
                    showToast("조건 불충족", "선택하신 조건에 맞는 시간표 조합이 없습니다.", "error");
                    // 롤백 (선택 취소)
                    courseFilters.delete(courseName);
                } else {
                    renderSchedule(filteredIndices[0]);
                }
                
            } else {
                // 이미 핀된 강의 클릭 -> 다른 시간대로 로테이션 (Rotate)
                
                // 1. 현재 강의 제외한 나머지 필터 조건 준비
                const otherFilters = new Map(courseFilters);
                otherFilters.delete(courseName);
                
                // 2. 나머지 조건에 맞는 스케줄만 탐색하여, 해당 강의의 가능한 '다른 시간대' 목록 수집
                const availableTimeSlots = new Set();
                
                for (const s of schedules) {
                    // 나머지 필터 조건 확인
                    let matchesOthers = true;
                    for (const [filterName, filterTime] of otherFilters) {
                        const c = s.courses.find(course => course.name === filterName);
                        let state = 'NONE';
                        if (c && c.time_slots.length > 0) {
                            state = `${c.time_slots[0].day} ${c.time_slots[0].start_time}`;
                        }
                        if (state !== filterTime) {
                            matchesOthers = false;
                            break;
                        }
                    }
                    
                    if (matchesOthers) {
                        // 조건에 맞으면, 대상 강의(courseName)의 시간대 수집
                        const c = s.courses.find(course => course.name === courseName);
                        if (c && c.time_slots.length > 0) {
                            const timeKey = `${c.time_slots[0].day} ${c.time_slots[0].start_time}`;
                            availableTimeSlots.add(timeKey);
                        }
                    }
                }
                
                // 3. 정렬 (요일, 시간 순) -> 순환을 위해
                const sortedSlots = Array.from(availableTimeSlots).sort();
                
                if (sortedSlots.length <= 1) {
                    // [개선된 로직] 원인 파악 (분반이 하나뿐 vs 충돌)
                    const totalSlots = new Set();
                     for (const s of schedules) {
                        const c = s.courses.find(course => course.name === courseName);
                        if (c && c.time_slots.length > 0) {
                             const timeKey = `${c.time_slots[0].day} ${c.time_slots[0].start_time}`;
                             totalSlots.add(timeKey);
                        }
                     }
                    
                    if (totalSlots.size <= 1) {
                         showToast(
                            "유일한 시간대입니다.",
                            "이 강의는 개설된 분반이 하나뿐이라 이동할 수 없습니다.",
                            "error"
                        );
                    } else {
                         showToast(
                            "이동 불가 (시간 중복)",
                            "다른 분반이 존재하지만, 현재 설정된 조건(필수/고정 강의)과 시간이 겹쳐 이동할 수 없습니다.",
                            "error"
                        );
                    }
                    return;
                }
                
                // 4. 현재 시간 다음 순번 찾기
                const currentTime = courseFilters.get(courseName);
                let currentIdx = sortedSlots.indexOf(currentTime);
                let nextIdx = (currentIdx + 1) % sortedSlots.length;
                let nextTime = sortedSlots[nextIdx];
                
                // 5. 필터 업데이트 및 적용
                courseFilters.set(courseName, nextTime);
                console.log(`Rotated ${courseName}: ${currentTime} -> ${nextTime}`);
                
                // 필터 적용 (위에서 이미 로직이 있으므로 재활용하거나 새로 작성)
                // 여기선 간단히 전체 재검색 (성능 이슈 없음)
                const newFilteredIndices = [];
                for (let i = 0; i < schedules.length; i++) {
                    const s = schedules[i];
                    let matchesAll = true;
                    
                    for (const [filterName, filterTime] of courseFilters) {
                        const c = s.courses.find(course => course.name === filterName);
                        let state = 'NONE';
                        if (c && c.time_slots.length > 0) {
                            state = `${c.time_slots[0].day} ${c.time_slots[0].start_time}`;
                        }
                        if (state !== filterTime) {
                            matchesAll = false;
                            break;
                        }
                    }
                    
                    if (matchesAll) {
                        newFilteredIndices.push(i);
                    }
                }
                
                filteredIndices = newFilteredIndices;
                filteredPosition = 0;
                
                if (filteredIndices.length > 0) {
                    renderSchedule(filteredIndices[0]);
                } else {
                    // 이론상 여기 도달하면 안됨 (availableTimeSlots에서 가져왔으므로)
                     showToast("시스템 오류", "해당 시간표를 찾을 수 없습니다.", "error");
                     courseFilters.set(courseName, currentTime); // 롤백
                }
            }
        }
        
        // 초기 렌더링
        renderSchedule(0);
    </script>
</body>
</html>
"""

    @staticmethod
    def generate_html(
        schedules: List[Schedule], 
        output_file: str, 
        required_course_names: set = None,
        desired_course_names: set = None,
        year: str = None,
        semester: str = None
    ):
        """
        시간표 조합 결과를 인터랙티브 HTML 파일로 저장
        
        Args:
            schedules: 생성된 Schedule 객체 리스트
            output_file: 저장할 파일 경로
            required_course_names: 필수 강의명 집합 (시각적 강조용)
            desired_course_names: 희망 강의명 집합 (전체 목록 표시용)
        """
        if not schedules:
            print("❌ 생성된 시간표가 없어 HTML을 생성하지 않습니다.")
            return

        # 1. 무작위 셔플 (다양한 결과를 먼저 보여주기 위해)
        # 10000개 이상이면 셔플링하는데 비용이 들 수 있지만, UX를 위해 진행

        shuffled_schedules = schedules.copy()
        
        # 결과가 너무 많으면 10,000개만 샘플링 (브라우저 성능 고려)
        if len(shuffled_schedules) > 10000:
            print(f"⚠️  결과가 너무 많아 10,000개만 랜덤 추출하여 시각화합니다.")
            shuffled_schedules = random.sample(shuffled_schedules, 10000)
        else:
            random.shuffle(shuffled_schedules)
            
        # 2. 데이터 직렬화 (JSON)
        # Schedule -> dict 변환
        schedule_data = []
        for s in shuffled_schedules:
            courses_data = []
            for c in s.courses:
                courses_data.append({
                    "name": c.name,
                    "credits": c.credits,
                    "professor": c.professor,
                    "time_slots": [
                        {"day": t.day, "start_time": t.start_time, "end_time": t.end_time}
                        for t in c.time_slots
                    ]
                })
            
            schedule_data.append({
                "courses": courses_data,
                "total_credits": s.total_credits,
                "has_random_filled": getattr(s, 'has_random_filled', False)
            })
            
        json_str = json.dumps(schedule_data, ensure_ascii=False)
        
        # 3. 전체 강의 목록 준비 (사이드바용)
        if required_course_names is None: required_course_names = set()
        if desired_course_names is None: desired_course_names = set()
        
        # 결과에 있는 강의 + 설정에 있는 강의 합집합
        all_names = set(desired_course_names) | set(required_course_names)
        
        # 결과에 실제로 등장하는 강의들도 추가 (혹시 모르니)
        for s in shuffled_schedules:
            for c in s.courses:
                all_names.add(c.name)
                
        all_courses_json = json.dumps(list(all_names), ensure_ascii=False)
        required_courses_json = json.dumps(list(required_course_names), ensure_ascii=False)
        
        # 4. HTML 생성
        final_html = HtmlVisualizer.HTML_TEMPLATE.replace('SCHEDULE_DATA_PLACEHOLDER', json_str)
        final_html = final_html.replace('ALL_COURSES_PLACEHOLDER', all_courses_json)
        final_html = final_html.replace('REQUIRED_COURSES_PLACEHOLDER', required_courses_json)

        term_label = ""
        if year and semester:
            term_label = f"{year}학년도 {semester}학기"
        elif year:
            term_label = f"{year}학년도"

        if term_label:
            final_html = final_html.replace(
                "<title>시간표 조합 결과</title>",
                f"<title>{term_label} 시간표 조합 결과</title>"
            )
            final_html = final_html.replace(
                '<div class="header">',
                f'<div class="header">\n            <div style="font-size: 1rem; opacity: 0.9; margin-bottom: 8px;">{term_label}</div>',
                1
            )
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(final_html)
            
        print(f"✅ HTML 시각화 파일 생성 완료: {output_file}")


def generate_html(schedules, output_file, required_names=None, desired_names=None, year=None, semester=None):
    """Wrapper."""
    HtmlVisualizer.generate_html(
        schedules,
        output_file,
        required_names,
        desired_names,
        year=year,
        semester=semester
    )
