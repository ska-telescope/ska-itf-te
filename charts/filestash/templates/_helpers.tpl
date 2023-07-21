{{/*
Expand the name of the chart.
*/}}
{{- define "filestash.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Create a default fully qualified app name.
We truncate at 63 chars because some Kubernetes name fields are limited to this (by the DNS naming spec).
If release name contains chart name it will be used as a full name.
*/}}
{{- define "filestash.fullname" -}}
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
{{- define "filestash.chart" -}}
{{- printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Common labels
*/}}
{{- define "filestash.labels" -}}
helm.sh/chart: {{ include "filestash.chart" . }}
{{ include "filestash.selectorLabels" . }}
{{- if .Chart.AppVersion }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
{{- end }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end }}
{{/*
Test-labels
*/}}
{{- define "filestash.test-labels" -}}
helm.sh/chart: {{ include "filestash.chart" . }}
app.kubernetes.io/name: {{ include "filestash.name" . }}-test-connection
app.kubernetes.io/instance: {{ .Release.Name }}
{{- if .Chart.AppVersion }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
{{- end }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end }}

{{/*
Selector labels
*/}}
{{- define "filestash.selectorLabels" -}}
app.kubernetes.io/name: {{ include "filestash.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}

{{/*
Create the name of the service account to use
*/}}
{{- define "filestash.serviceAccountName" -}}
{{- if .Values.serviceAccount.create }}
{{- default (include "filestash.fullname" .) .Values.serviceAccount.name }}
{{- else }}
{{- default "default" .Values.serviceAccount.name }}
{{- end }}
{{- end }}
{{/*
set the image pull policy based on the current environment
in dev environment image pull policy will always be never
*/}}
{{- define "filestash.pullPolicy" }}
{{- if .Values.imageoverride -}}
IfNotPresent
{{- else if eq .Values.env.type "production" -}}
{{ .Values.imagePullPolicy }}
{{- else if eq .Values.env.type "ci" -}}
Always
{{- else -}}
IfNotPresent
{{- end }}
{{- end }}
{{/*
set the filestash serviceType
*/}}
{{- define "filestash.serviceType" }}
{{- if eq .Values.env.type "dev" -}}
NodePort
{{- else -}}
LoadBalancer
{{- end }}
{{- end }}
{{/*
set the filestash image
*/}}
{{- define "filestash.image" -}}
{{- if .Values.imageoverride -}}
{{ .Values.imageoverride }}
{{- else if .Values.image.repository  -}}
'{{ .Values.image.repository }}/{{ .Values.image.name }}:{{ .Values.image.tag }}'
{{- else -}}
'{{ .Values.image.name }}:{{ .Values.image.tag }}'
{{- end }}
{{- end }}
{{/*
set the filestash init image
*/}}
{{- define "filestash.initImage" -}}
{{- if .Values.image.repository  -}}
'{{ .Values.image.repository }}/{{ .Values.image.init }}:{{ .Values.image.tag }}'
{{- else -}}
'{{ .Values.image.init }}:{{ .Values.image.tag }}'
{{- end }}
{{- end }}
{{/*
Storage class
*/}}
*/}}
{{- define "filestash.storageClass" }}
{{- if eq .Values.env.type "dev" -}}
hostpath
{{- else -}}
nfss1
{{- end }}
{{- end }}