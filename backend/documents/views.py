from django.core.exceptions import ValidationError as DjangoValidationError
from django.http import FileResponse, Http404
from django.shortcuts import get_object_or_404

from rest_framework import generics, status
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response

from users.permissions import IsBranchManager, IsInstructor, IsSuperAdmin

from .models import Document
from .permissions import can_delete, can_upload, documents_for
from .serializers import DocumentSerializer, DocumentUploadSerializer

# All three roles share the document screens; scope is what separates them.
ANY_STAFF = [IsSuperAdmin | IsBranchManager | IsInstructor]


class DocumentListCreateView(generics.ListCreateAPIView):
    permission_classes = ANY_STAFF

    def get_serializer_class(self):
        return DocumentUploadSerializer if self.request.method == "POST" else DocumentSerializer

    def get_serializer_context(self):
        return {"request": self.request}

    def get_queryset(self):
        qs = documents_for(self.request.user)
        params = self.request.query_params

        scope = params.get("scope")
        if scope == "organisation":
            qs = qs.filter(branch__isnull=True, participant__isnull=True)
        elif scope == "branch":
            qs = qs.filter(branch__isnull=False)
        elif scope == "participant":
            qs = qs.filter(participant__isnull=False)

        branch = params.get("branch")
        if branch:
            try:
                qs = qs.filter(branch_id=branch)
            except (DjangoValidationError, ValueError):
                return qs.none()

        participant = params.get("participant")
        if participant:
            try:
                qs = qs.filter(participant_id=participant)
            except (DjangoValidationError, ValueError):
                return qs.none()

        return qs

    def perform_create(self, serializer):
        branch = serializer.validated_data.get("branch")
        participant = serializer.validated_data.get("participant")
        if not can_upload(self.request.user, branch, participant):
            raise PermissionDenied("You cannot upload a document to this scope.")

        upload = serializer.validated_data.pop("file")
        serializer.save(
            file=upload, name=upload.name, size=upload.size, uploaded_by=self.request.user,
        )

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        # Return the read shape so the frontend list can insert the row directly.
        data = DocumentSerializer(serializer.instance, context=self.get_serializer_context()).data
        return Response(data, status=status.HTTP_201_CREATED)


class DocumentDetailView(generics.DestroyAPIView):
    permission_classes = ANY_STAFF
    serializer_class = DocumentSerializer

    def get_queryset(self):
        return documents_for(self.request.user)

    def destroy(self, request, *args, **kwargs):
        document = self.get_object()
        if not can_delete(request.user, document):
            raise PermissionDenied("You cannot delete this document.")
        document.file.delete(save=False)
        document.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class DocumentDownloadView(generics.GenericAPIView):
    permission_classes = ANY_STAFF

    def get(self, request, pk):
        document = get_object_or_404(documents_for(request.user), pk=pk)
        try:
            opened = document.file.open("rb")
        except FileNotFoundError:
            raise Http404
        response = FileResponse(opened, as_attachment=True, filename=document.name)
        response["Cache-Control"] = "private, no-store"
        response["X-Content-Type-Options"] = "nosniff"
        return response
