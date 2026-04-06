from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import and_, func, select
from sqlalchemy.orm import Session, selectinload

from app import schemas
from app.access import is_admin_user
from app.db import get_db
from app.dependencies import get_admin_user, get_current_user, get_optional_user
from app.models import Professor, Review, User


router = APIRouter(prefix="/api", tags=["professors"])


@router.get("/professors", response_model=list[schemas.ProfessorRead])
def list_professors(db: Session = Depends(get_db)):
    stmt = (
        select(
            Professor.id,
            Professor.name,
            Professor.department,
            Professor.photo_url,
            Professor.created_at,
            func.avg(Review.rating).label("average_rating"),
            func.count(Review.id).label("review_count"),
        )
        .outerjoin(
            Review,
            and_(
                Review.professor_id == Professor.id,
                Review.is_deleted.is_(False),
            ),
        )
        .group_by(Professor.id)
        .order_by(Professor.name.asc())
    )
    rows = db.execute(stmt).all()

    return [
        schemas.ProfessorRead(
            id=row.id,
            name=row.name,
            department=row.department,
            photo_url=row.photo_url,
            created_at=row.created_at,
            average_rating=float(row.average_rating) if row.average_rating is not None else None,
            review_count=int(row.review_count),
        )
        for row in rows
    ]


@router.post(
    "/professors",
    response_model=schemas.ProfessorRead,
    status_code=status.HTTP_201_CREATED,
)
def create_professor(
    payload: schemas.ProfessorCreate,
    db: Session = Depends(get_db),
    _admin_user: User = Depends(get_admin_user),
):

    existing = db.execute(
        select(Professor).where(func.lower(Professor.name) == payload.name.lower())
    ).scalar_one_or_none()
    if existing:
        raise HTTPException(status_code=409, detail="A professor with this name already exists.")

    professor = Professor(name=payload.name, department=payload.department, photo_url=payload.photo_url)
    db.add(professor)
    db.commit()
    db.refresh(professor)

    return schemas.ProfessorRead(
        id=professor.id,
        name=professor.name,
        department=professor.department,
        photo_url=professor.photo_url,
        created_at=professor.created_at,
        average_rating=None,
        review_count=0,
    )


@router.put("/professors/{professor_id}", response_model=schemas.ProfessorRead)
def update_professor(
    professor_id: int,
    payload: schemas.ProfessorCreate,
    db: Session = Depends(get_db),
    _admin_user: User = Depends(get_admin_user),
):
    professor = db.get(Professor, professor_id)
    if professor is None:
        raise HTTPException(status_code=404, detail="Professor not found.")

    existing = db.execute(
        select(Professor).where(
            func.lower(Professor.name) == payload.name.lower(),
            Professor.id != professor_id,
        )
    ).scalar_one_or_none()
    if existing:
        raise HTTPException(status_code=409, detail="A professor with this name already exists.")

    professor.name = payload.name
    professor.department = payload.department
    professor.photo_url = payload.photo_url
    db.commit()
    db.refresh(professor)

    stats = db.execute(
        select(
            func.avg(Review.rating),
            func.count(Review.id),
        ).where(
            Review.professor_id == professor.id,
            Review.is_deleted.is_(False),
        )
    ).one()

    avg_rating, review_count = stats
    return schemas.ProfessorRead(
        id=professor.id,
        name=professor.name,
        department=professor.department,
        photo_url=professor.photo_url,
        created_at=professor.created_at,
        average_rating=float(avg_rating) if avg_rating is not None else None,
        review_count=int(review_count),
    )


@router.delete("/professors/{professor_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_professor(
    professor_id: int,
    db: Session = Depends(get_db),
    _admin_user: User = Depends(get_admin_user),
):
    professor = db.get(Professor, professor_id)
    if professor is None:
        raise HTTPException(status_code=404, detail="Professor not found.")

    db.delete(professor)
    db.commit()


@router.delete("/reviews/{review_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_review(
    review_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    review = db.get(Review, review_id)
    if review is None:
        raise HTTPException(status_code=404, detail="Review not found.")

    can_delete = is_admin_user(current_user) or review.user_id == current_user.id
    if not can_delete:
        raise HTTPException(status_code=403, detail="You can only delete your own review.")

    if review.is_deleted:
        return

    review.is_deleted = True
    review.deleted_at = datetime.now(timezone.utc)
    db.commit()


@router.get("/professors/{professor_id}", response_model=schemas.ProfessorDetails)
def get_professor_details(
    professor_id: int,
    db: Session = Depends(get_db),
    current_user: User | None = Depends(get_optional_user),
):
    stmt = (
        select(Professor)
        .where(Professor.id == professor_id)
        .options(selectinload(Professor.reviews).selectinload(Review.reviewer))
    )
    professor = db.execute(stmt).scalar_one_or_none()

    if professor is None:
        raise HTTPException(status_code=404, detail="Professor not found.")

    is_admin = is_admin_user(current_user)

    visible_reviews = professor.reviews
    if not is_admin:
        visible_reviews = [review for review in professor.reviews if not review.is_deleted]

    reviews_sorted = sorted(
        visible_reviews,
        key=lambda review: review.created_at,
        reverse=True,
    )

    can_view_reviewer_emails = is_admin

    review_models = [
        schemas.ReviewRead(
            id=review.id,
            rating=review.rating,
            review_text=review.review_text,
            created_at=review.created_at,
            is_deleted=review.is_deleted,
            reviewer=schemas.UserPublic(
                id=review.reviewer.id,
                username=review.reviewer.username or "anonymous",
                email=review.reviewer.email if can_view_reviewer_emails else None,
            ),
        )
        for review in reviews_sorted
    ]

    average_rating = None
    if reviews_sorted:
        average_rating = round(
            sum(review.rating for review in reviews_sorted if not review.is_deleted)
            / len([review for review in reviews_sorted if not review.is_deleted]),
            2,
        ) if any(not review.is_deleted for review in reviews_sorted) else None

    return schemas.ProfessorDetails(
        id=professor.id,
        name=professor.name,
        department=professor.department,
        photo_url=professor.photo_url,
        created_at=professor.created_at,
        average_rating=average_rating,
        review_count=len([review for review in reviews_sorted if not review.is_deleted]),
        reviews=review_models,
    )


@router.post(
    "/professors/{professor_id}/reviews",
    response_model=schemas.ReviewRead,
    status_code=status.HTTP_201_CREATED,
)
def create_review(
    professor_id: int,
    payload: schemas.ReviewCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not current_user.username:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Set a username before posting reviews.",
        )

    professor = db.get(Professor, professor_id)
    if professor is None:
        raise HTTPException(status_code=404, detail="Professor not found.")

    existing = db.execute(
        select(Review).where(
            Review.professor_id == professor_id,
            Review.user_id == current_user.id,
        )
    ).scalar_one_or_none()
    if existing and not existing.is_deleted:
        raise HTTPException(status_code=409, detail="You already reviewed this professor.")

    if existing and existing.is_deleted:
        existing.rating = payload.rating
        existing.review_text = payload.review_text
        existing.is_deleted = False
        existing.deleted_at = None
        review = existing
    else:
        review = Review(
            rating=payload.rating,
            review_text=payload.review_text,
            user_id=current_user.id,
            professor_id=professor.id,
        )
        db.add(review)

    db.commit()
    db.refresh(review)

    return schemas.ReviewRead(
        id=review.id,
        rating=review.rating,
        review_text=review.review_text,
        created_at=review.created_at,
        is_deleted=review.is_deleted,
        reviewer=schemas.UserPublic(
            id=current_user.id,
            username=current_user.username,
            email=current_user.email if is_admin_user(current_user) else None,
        ),
    )
