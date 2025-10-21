from django.db import models


class JobTitle(models.Model):
    name = models.CharField(max_length=200)

class CV(models.Model):
    name = models.CharField(max_length=200)
    job_title = models.ForeignKey(JobTitle, on_delete=models.CASCADE)
    years_of_experience = models.IntegerField()
    skills = models.TextField()
    education = models.TextField()
    past_experience = models.TextField()
