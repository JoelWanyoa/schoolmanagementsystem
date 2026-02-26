# timetabling/generator.py
import random
from datetime import time
from django.utils import timezone
from django.db.models import Q
from collections import defaultdict
from core.models import Timetable, Subject, Teacher, ClassSubject, AcademicYear, Section, Class

class TimetableGenerator:
    def __init__(self, class_level, section, academic_year=None):
        self.class_level = class_level
        self.section = section
        self.academic_year = academic_year
        self.periods = []
        self.teachers_availability = defaultdict(set)
        self.subjects_assigned = defaultdict(int)
        # Tracking to ensure diversity: same teacher should not be in the same period more than once a week if possible
        self.period_teacher_history = defaultdict(set) # period_number -> set of teacher_ids
        self.max_periods_per_day = 8
        self.break_periods = [3, 6]  # Break after 3rd and 6th period
        
    def generate_timetable(self):
        """Generate complete timetable for the class section"""
        try:
            # Clear existing timetable for this class section
            Timetable.objects.filter(
                class_level=self.class_level, 
                section=self.section
            ).delete()
            
            # Get subjects assigned to this class and section
            self.class_subjects = ClassSubject.objects.filter(
                class_level=self.class_level,
                section=self.section
            ).select_related('subject', 'teacher')
            
            if not self.class_subjects.exists():
                # Fallback to all subjects if no specific assignments
                subjects = Subject.objects.all()
                self.subject_pool = []
                for sub in subjects:
                    self.subject_pool.extend([sub] * 5) # Default 5 periods each
            else:
                # Build subject pool based on weekly periods
                self.subject_pool = []
                for cs in self.class_subjects:
                    self.subject_pool.extend([cs.subject] * cs.weekly_periods)
            
            random.shuffle(self.subject_pool)
            
            # Map subjects to their preferred teachers from ClassSubject
            self.subject_teacher_map = {}
            for cs in self.class_subjects:
                self.subject_teacher_map[cs.subject.id] = cs.teacher
                
            # Get all available teachers for backup
            self.all_subject_teachers = self._get_all_subject_teachers()
            
            # Define periods structure
            self._define_periods_structure()
            
            # Generate timetable for each day (Monday to Saturday)
            # Shuffle days order so we don't always fill Monday first
            days = list(Timetable.DAY_CHOICES)
            # random.shuffle(days) # Actually, better to keep chronological for predictability in some cases, 
            # but shuffling subjects within the day is enough.
            
            for day_code, day_name in days:
                self._generate_daily_timetable(day_code)
            
            return True, "Timetable generated successfully with improved shuffling"
            
        except Exception as e:
            import traceback
            print(f"ERROR generating timetable: {str(e)}")
            traceback.print_exc()
            return False, f"Error generating timetable: {str(e)}"
    
    def _get_all_subject_teachers(self):
        """Pre-fetch all potential teachers for subjects"""
        subject_teachers = defaultdict(list)
        teachers = Teacher.objects.filter(is_active=True).prefetch_related('subjects')
        for teacher in teachers:
            for subject in teacher.subjects.all():
                subject_teachers[subject.id].append(teacher)
        return subject_teachers
    
    def _define_periods_structure(self):
        """Define the periods structure with times matching the school standard"""
        # Standard academic periods
        self.periods = [
            {'number': 1, 'start_time': time(8, 0), 'end_time': time(8, 40), 'is_break': False},
            {'number': 2, 'start_time': time(8, 40), 'end_time': time(9, 20), 'is_break': False},
            {'number': 3, 'start_time': time(9, 20), 'end_time': time(10, 0), 'is_break': False},
            # Tea Break: 10:00 - 10:20
            {'number': 101, 'start_time': time(10, 0), 'end_time': time(10, 20), 'is_break': True, 'break_name': 'Tea Break'},
            {'number': 4, 'start_time': time(10, 20), 'end_time': time(11, 0), 'is_break': False},
            {'number': 5, 'start_time': time(11, 0), 'end_time': time(11, 40), 'is_break': False},
            # Short Break: 11:40 - 12:20
            {'number': 102, 'start_time': time(11, 40), 'end_time': time(12, 20), 'is_break': True, 'break_name': 'Short Break'},
            {'number': 6, 'start_time': time(12, 20), 'end_time': time(13, 0), 'is_break': False},
            # Lunch Break: 13:00 - 14:00
            {'number': 103, 'start_time': time(13, 0), 'end_time': time(14, 0), 'is_break': True, 'break_name': 'Lunch Break'},
            {'number': 7, 'start_time': time(14, 0), 'end_time': time(14, 40), 'is_break': False},
            {'number': 8, 'start_time': time(14, 40), 'end_time': time(15, 20), 'is_break': False},
            {'number': 9, 'start_time': time(15, 20), 'end_time': time(16, 0), 'is_break': False},
            # Games: 16:00 - 17:00
            {'number': 104, 'start_time': time(16, 0), 'end_time': time(17, 0), 'is_break': True, 'break_name': 'Games'}
        ]

    
    def _generate_daily_timetable(self, day):
        """Generate timetable for a specific day"""
        # Track teachers used in this specific day to avoid double-booking
        used_teachers_today = set()
        
        for period in self.periods:
            if period['is_break']:
                Timetable.objects.create(
                    class_level=self.class_level,
                    section=self.section,
                    day=day,
                    period_number=period['number'],
                    start_time=period['start_time'],
                    end_time=period['end_time'],
                    is_break=True,
                    break_name=period['break_name']
                )
                continue
            
            # Try to pick a subject from the pool that hasn't been used too much today
            subject = self._pick_subject_for_slot(day, period)
            
            if not subject:
                # No more specific subjects in pool, create study period
                self._create_empty_period(day, period)
                continue
                
            teacher = self._get_best_teacher(subject, day, period, used_teachers_today)
            
            if teacher:
                Timetable.objects.create(
                    class_level=self.class_level,
                    section=self.section,
                    subject=subject,
                    teacher=teacher,
                    day=day,
                    period_number=period['number'],
                    start_time=period['start_time'],
                    end_time=period['end_time'],
                    room=self._get_dynamic_room(day, period),
                    is_break=False
                )
                
                # Update tracking
                used_teachers_today.add(teacher.id)
                self.teachers_availability[teacher.id].add((day, period['number']))
                self.period_teacher_history[period['number']].add(teacher.id)
                
                # Remove assigned instance from pool
                if subject in self.subject_pool:
                    self.subject_pool.remove(subject)
            else:
                # No teacher available, return subject to pool and create empty
                self._create_empty_period(day, period)

    def _pick_subject_for_slot(self, day, period):
        """Pick a subject from the pool, avoiding repeats in the same day if possible"""
        if not self.subject_pool:
            return None
            
        # Get subjects already used today
        used_today = Timetable.objects.filter(
            class_level=self.class_level,
            section=self.section,
            day=day,
            is_break=False
        ).values_list('subject_id', flat=True)
        
        # Try to find a subject not used today yet
        candidates = [s for s in self.subject_pool if s.id not in used_today]
        if candidates:
            return random.choice(candidates)
        
        # If all subjects in pool already used today, just pick any from pool
        return random.choice(self.subject_pool)

    def _get_best_teacher(self, subject, day, period, used_today):
        """Find the best teacher for the subject at this slot"""
        preferred = self.subject_teacher_map.get(subject.id)
        candidates = self.all_subject_teachers.get(subject.id, [])
        
        if preferred and preferred in candidates:
            # Move preferred to front but don't strictly require if we want variety
            # Actually, schools usually want the assigned teacher if available
            teachers_to_try = [preferred] + [t for t in candidates if t != preferred]
        else:
            teachers_to_try = list(candidates)
            random.shuffle(teachers_to_try)
            
        for teacher in teachers_to_try:
            # Basic availability check
            if teacher.id in used_today: continue
            
            # Check if teacher is used in this class/slot in other days (Variety requested)
            if teacher.id in self.period_teacher_history[period['number']]:
                # If we have other options that haven't been in this slot, try them first
                # But if this is the only teacher for this subject, we might have to use them
                other_available = [t for t in teachers_to_try if t.id not in self.period_teacher_history[period['number']] and t.id not in used_today]
                if other_available:
                    return random.choice(other_available)
            
            # External conflict check (other classes)
            if not Timetable.objects.filter(teacher=teacher, day=day, period_number=period['number']).exists():
                return teacher
                
        return None

    def _get_dynamic_room(self, day, period):
        """Shuffle rooms to avoid same room every time"""
        base_rooms = ['Room 101', 'Room 102', 'Room 103', 'Room 104', 'Room 105', 'Lab 1', 'Library']
        # Try to get the section's allocated room if it exists
        if hasattr(self.section, 'room_number') and self.section.room_number:
            base_rooms.insert(0, self.section.room_number)
            
        return random.choice(base_rooms)

    def _create_empty_period(self, day, period):
        Timetable.objects.create(
            class_level=self.class_level,
            section=self.section,
            day=day,
            period_number=period['number'],
            start_time=period['start_time'],
            end_time=period['end_time'],
            room='Classroom',
            is_break=False,
            break_name='Study Period'
        )

class AdvancedTimetableGenerator(TimetableGenerator):
    """Advanced generator that uses a more complex shuffling algorithm"""
    def generate_optimized_timetable(self):
        # For now, let's just use the improved base generator as it's already quite diverse
        return self.generate_timetable()