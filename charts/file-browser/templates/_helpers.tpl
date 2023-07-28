{{/*
Expand the name of the chart.
*/}}
{{- define "fileBrowser.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Create a default fully qualified app name.
We truncate at 63 chars because some Kubernetes name fields are limited to this (by the DNS naming spec).
If release name contains chart name it will be used as a full name.
*/}}
{{- define "fileBrowser.fullname" -}}
{{- if .Values.fullnameOverride }}
{{- .Values.fullnameOverride | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- $name := default .Chart.Name .Values.nameOverride }}
{{- if contains $name .Release.Name }}
{{- .Release.Name | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- printf "%s-%s" .Release.Name $name | trunc 63 | trimSuffix "-" }}
{{- end }}
{{- end }}
{{- end }}

{{/*
Create chart name and version as used by the chart label.
*/}}
{{- define "fileBrowser.chart" -}}
{{- printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Common labels
*/}}
{{- define "fileBrowser.labels" -}}
helm.sh/chart: {{ include "fileBrowser.chart" . }}
{{ include "fileBrowser.selectorLabels" . }}
{{- if .Chart.AppVersion }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
{{- end }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end }}
{{/*
Test-labels
*/}}
{{- define "fileBrowser.test-labels" -}}
helm.sh/chart: {{ include "fileBrowser.chart" . }}
app.kubernetes.io/name: {{ include "fileBrowser.name" . }}-test-connection
app.kubernetes.io/instance: {{ .Release.Name }}
{{- if .Chart.AppVersion }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
{{- end }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end }}

{{/*
Selector labels
*/}}
{{- define "fileBrowser.selectorLabels" -}}
app.kubernetes.io/name: {{ include "fileBrowser.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}

{{/*
Set the image pull policy based on the current environment
*/}}
{{- define "fileBrowser.pullPolicy" }}
{{- if eq .Values.env.type "production" -}}
{{ .Values.imagePullPolicy }}
{{- else if eq .Values.env.type "ci" -}}
Always
{{- else -}}
IfNotPresent
{{- end }}
{{- end }}
{{/*
set the serviceType based on the environment.
*/}}
{{- define "fileBrowser.serviceType" }}
{{- if eq .Values.env.type "dev" -}}
NodePort
{{- else -}}
LoadBalancer
{{- end }}
{{- end }}
