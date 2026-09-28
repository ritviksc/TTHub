from django.core.exceptions import ValidationError as DjangoValidationError
from django.http import FileResponse, Http404
from django.shortcuts import get_object_or_404

from rest_framework import generics, status
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.response import Response

from users.permissions import IsBranchManager, IsInstructor, IsSuperAdmin

from .permissions import can_manage, can_manage_folder, can_manage_scope, can_upload, documents_for, folders_for
from .serializers import DocumentSerializer, DocumentUploadSerializer, FolderSerializer

# All three roles share the document screens; scope is what separates them.
ANY_STAFF = [IsSuperAdmin | IsBranchManager | IsInstructor]


def _filter_by_id(qs, field, value):
    """Apply an `<field>_id=value` filter, treating a malformed uuid as no matches."""
    try:
        return qs.filter(**{f"{field}_id": value})
    except (DjangoValidationError, ValueError):
        return qs.none()


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
            qs = _filter_by_id(qs, "branch", branch)

        participant = params.get("participant")
        if participant:
            qs = _filter_by_id(qs, "participant", participant)

        folder = params.get("folder")
        if folder == "root":
            qs = qs.filter(folder__isnull=True)
        elif folder:
            qs = _filter_by_id(qs, "folder", folder)

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


class DocumentDetailView(generics.RetrieveUpdateDestroyAPIView):
    """GET to read, PATCH to rename or move (change `folder`), DELETE to remove."""

    permission_classes = ANY_STAFF
    serializer_class = DocumentSerializer

    def get_queryset(self):
        return documents_for(self.request.user)

    def get_serializer_context(self):
        return {"request": self.request}

    def perform_update(self, serializer):
        document = serializer.instance
        if not can_manage(self.request.user, document):
            raise PermissionDenied("You cannot rename or move this document.")

        if "folder" in serializer.validated_data:
            folder = serializer.validated_data["folder"]
            if document.participant_id and folder is not None:
                raise ValidationError({"folder": "A participant's document cannot be filed in a folder."})
            if folder is not None and folder.branch_id != document.branch_id:
                raise ValidationError({"folder": "A document cannot move to a different branch or scope."})

        serializer.save()

    def destroy(self, request, *args, **kwargs):
        document = self.get_object()
        if not can_manage(request.user, document):
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


class FolderListCreateView(generics.ListCreateAPIView):
    """GET ?branch=<id> or ?scope=organisation lists every folder in that scope.

    There are only ever a handful of folders per branch, so the frontend fetches
    them flat, in one call, and builds the tree client-side.
    """

    permission_classes = ANY_STAFF
    serializer_class = FolderSerializer

    def get_serializer_context(self):
        return {"request": self.request}

    def get_queryset(self):
        qs = folders_for(self.request.user)
        params = self.request.query_params

        if params.get("scope") == "organisation":
            return qs.filter(branch__isnull=True)

        branch = params.get("branch")
        if branch:
            return _filter_by_id(qs, "branch", branch)

        return qs.none()

    def perform_create(self, serializer):
        branch = serializer.validated_data.get("branch")
        branch_id = branch.pk if branch else None
        if not can_manage_scope(self.request.user, branch_id):
            raise PermissionDenied("You cannot create a folder in this scope.")
        serializer.save(created_by=self.request.user)


class FolderDetailView(generics.RetrieveUpdateDestroyAPIView):
    """GET to read, PATCH to rename or move (change `parent`), DELETE once empty."""

    permission_classes = ANY_STAFF
    serializer_class = FolderSerializer

    def get_queryset(self):
        return folders_for(self.request.user)

    def get_serializer_context(self):
        return {"request": self.request}

    def perform_update(self, serializer):
        folder = serializer.instance
        if not can_manage_folder(self.request.user, folder):
            raise PermissionDenied("You cannot rename or move this folder.")
        serializer.save()

    def destroy(self, request, *args, **kwargs):
        folder = self.get_object()
        if not can_manage_folder(request.user, folder):
            raise PermissionDenied("You cannot delete this folder.")
        if folder.children.exists() or folder.documents.exists():
            return Response(
                {"detail": "Move or delete its contents first."},
                status=status.HTTP_409_CONFLICT,
            )
        folder.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
