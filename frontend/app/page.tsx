"use client";

import React, { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Slider } from "@/components/ui/slider";
import { Input } from "@/components/ui/input";
import { Activity, AlertTriangle, Utensils, Dumbbell, CheckCircle2 } from "lucide-react";
import { fetchHealthPlan, type HealthPlan } from "@/lib/api";

export default function PulseAIDashboard() {
  const [symptoms, setSymptoms] = useState("");
  const [painScale, setPainScale] = useState<number[]>([5]);
  const [bodyPhoto, setBodyPhoto] = useState<File | null>(null);
  const [bloodTestPdf, setBloodTestPdf] = useState<File | null>(null);
  const [loading, setLoading] = useState(false);
  const [plan, setPlan] = useState<HealthPlan | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setErrorMessage(null);

    try {
      const data = await fetchHealthPlan({
        symptoms,
        painScale: painScale[0],
        bodyPhoto,
        bloodTestPdf,
      });
      setPlan(data);
    } catch (error) {
      console.error("Failed to fetch health plan:", error);
      setErrorMessage(
        error instanceof Error ? error.message : "The health assessment failed.",
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-50 dark:bg-slate-950 p-6 text-slate-900 dark:text-slate-100">
      {/* Header */}
      <header className="mb-8 flex items-center justify-between border-b border-slate-200 dark:border-slate-800 pb-4">
        <div>
          <h1 className="text-3xl font-bold flex items-center gap-2">
            <Activity className="h-8 w-8 text-blue-600" /> PulseAI
          </h1>
          <p className="text-slate-500 dark:text-slate-400 text-sm">
            AI-Powered Personal Health, Nutrition & Workout Assistant
          </p>
        </div>
      </header>

      {/* Main Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        
        {/* Left Side: Intake Form */}
        <Card className="shadow-sm border-slate-200 dark:border-slate-800">
          <CardHeader>
            <CardTitle>Health Intake & Assessment</CardTitle>
            <CardDescription>Enter current symptoms and upload recent lab tests or physical photos.</CardDescription>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleSubmit} className="space-y-6">
              <div>
                <label className="block text-sm font-medium mb-2">Describe Symptoms or Feelings</label>
                <Textarea 
                  placeholder="e.g., Lower back tightness after workouts, slight fatigue in afternoons..." 
                  value={symptoms}
                  onChange={(e) => setSymptoms(e.target.value)}
                  className="h-28"
                  required
                />
              </div>

              <div>
                <label className="block text-sm font-medium mb-2">Pain / Discomfort Scale ({painScale[0]}/10)</label>
                <Slider 
                  value={painScale} 
                  onValueChange={(val) => {
                    const numArr = Array.isArray(val) ? val : [val];
                    setPainScale(numArr.map(Number));
                  }} 
                  max={10} 
                  step={1} 
                />
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-medium mb-1 text-slate-500">Body / Posture Photo</label>
                  <Input 
                    type="file" 
                    accept="image/*" 
                    onChange={(e) => setBodyPhoto(e.target.files?.[0] || null)}
                  />
                </div>
                <div>
                  <label className="block text-xs font-medium mb-1 text-slate-500">Blood Test PDF</label>
                  <Input 
                    type="file" 
                    accept=".pdf" 
                    onChange={(e) => setBloodTestPdf(e.target.files?.[0] || null)}
                  />
                </div>
              </div>

              <Button type="submit" className="w-full bg-blue-600 hover:bg-blue-700 text-white" disabled={loading}>
                {loading ? "Generating local AI assessment..." : "Generate AI Health Plan"}
              </Button>
              {errorMessage && (
                <p role="alert" className="text-sm text-red-600">
                  {errorMessage}
                </p>
              )}
            </form>
          </CardContent>
        </Card>

        {/* Right Side: AI Generated Plan */}
        <div className="space-y-6">
          {plan ? (
            <>
              {/* Health Observations Card */}
              <Card className="border-amber-200 bg-amber-50/50 dark:bg-amber-950/20 dark:border-amber-900">
                <CardHeader className="flex flex-row items-center gap-2 pb-2">
                  <AlertTriangle className="h-5 w-5 text-amber-600" />
                  <CardTitle className="text-amber-900 dark:text-amber-300 text-base">Key AI Observations</CardTitle>
                </CardHeader>
                <CardContent className="space-y-2">
                  <p className="text-sm text-amber-900 dark:text-amber-200">{plan.assessment}</p>
                  {plan.concerns.map((item, idx) => (
                    <div key={idx} className="border-b border-amber-200/60 dark:border-amber-900/40 pb-2 last:border-0 last:pb-0">
                      <p className="font-semibold text-amber-900 dark:text-amber-200 text-sm">{item.title}</p>
                      <p className="text-xs text-amber-800 dark:text-amber-400">{item.desc}</p>
                    </div>
                  ))}
                  <p className="pt-2 text-xs text-amber-800 dark:text-amber-400">
                    <strong>When to seek care:</strong> {plan.urgent_care}
                  </p>
                </CardContent>
              </Card>

              {/* Nutrition Card */}
              <Card className="border-slate-200 dark:border-slate-800">
                <CardHeader className="flex flex-row items-center gap-2 pb-2">
                  <Utensils className="h-5 w-5 text-emerald-600" />
                  <CardTitle className="text-base">Target Daily Macros</CardTitle>
                </CardHeader>
                <CardContent className="grid grid-cols-4 gap-2 text-center">
                  <div className="bg-slate-100 dark:bg-slate-800 p-2 rounded"><p className="text-xs text-slate-500">Calories</p><p className="font-bold text-sm">{plan.nutrition.calories ?? "—"}</p></div>
                  <div className="bg-slate-100 dark:bg-slate-800 p-2 rounded"><p className="text-xs text-slate-500">Protein</p><p className="font-bold text-sm">{plan.nutrition.protein ?? "—"}</p></div>
                  <div className="bg-slate-100 dark:bg-slate-800 p-2 rounded"><p className="text-xs text-slate-500">Carbs</p><p className="font-bold text-sm">{plan.nutrition.carbs ?? "—"}</p></div>
                  <div className="bg-slate-100 dark:bg-slate-800 p-2 rounded"><p className="text-xs text-slate-500">Fats</p><p className="font-bold text-sm">{plan.nutrition.fats ?? "—"}</p></div>
                  <p className="col-span-4 text-xs text-slate-500">{plan.nutrition.notes}</p>
                </CardContent>
              </Card>

              {/* Workout Card */}
              <Card className="border-slate-200 dark:border-slate-800">
                <CardHeader className="flex flex-row items-center gap-2 pb-2">
                  <Dumbbell className="h-5 w-5 text-blue-600" />
                  <CardTitle className="text-base">Tailored Workout Focus</CardTitle>
                </CardHeader>
                <CardContent>
                  <p className="text-sm text-slate-700 dark:text-slate-300">{plan.workout}</p>
                  <p className="mt-3 text-xs text-slate-500">{plan.limitations}</p>
                  <p className="mt-2 text-xs text-slate-500">
                    General wellness information only; this is not a diagnosis or a substitute for professional medical care.
                  </p>
                </CardContent>
              </Card>
            </>
          ) : (
            <Card className="border-dashed border-slate-300 dark:border-slate-800 h-full flex items-center justify-center p-8 text-center text-slate-400 min-h-[350px]">
              <div className="flex flex-col items-center gap-2">
                <CheckCircle2 className="h-10 w-10 text-slate-300 dark:text-slate-700" />
                <p className="text-sm">Submit your symptoms and uploads to get a locally generated assessment and recommendations.</p>
              </div>
            </Card>
          )}
        </div>

      </div>
    </div>
  );
}