from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from tourplan.models import Student
from django.views.generic import TemplateView, CreateView
from django.contrib import messages
# Create your views here.

class TourStudentList(TemplateView):
    template_name = "tourplan/student_list.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["students"] = Student.objects.all().order_by("student_semester", "serial_number")
        context["semesters"] = range(1, 9)
        return context
    
    def post(self, request,*args, **kwargs):
        semester = request.POST.get('semester')
        rollno = request.POST.get('rollno')
        full_name = request.POST.get('fullname')
        participation = request.POST.get('participation') == 'true'

        if semester and rollno and full_name:
            try:
                Student.objects.create(
                    student_semester = int(semester),
                    serial_number = int(rollno),
                    student_name = full_name,
                    participation=participation
                )
                messages.success(request,"Participation recorded")
            except Exception as e :
                return messages.error(self,e)
        else:
            messages.warning(request, "Please all fields.")
        return redirect('core:tourplan')




    

