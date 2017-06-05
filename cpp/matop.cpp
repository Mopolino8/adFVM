#include "matop.hpp"
#define nrhs 5

Matop::Matop(RCF* rcf) {
    const Mesh& mesh = *(rcf->mesh);

    for (auto& patch: mesh.boundary) {
        auto& patchInfo = patch.second;
        integer startFace, nFaces;
        tie(startFace, nFaces) = mesh.boundaryFaces.at(patch.first);
        if (startFace >= mesh.nLocalFaces && nFaces > 0) {
            ivec tmp(nFaces, patchInfo.at("loc_neighbourIndices"));
            //cout << patch.first << tmp(0) << " " << tmp(1) << endl;
            boundaryNeighbours[patch.first] = tmp;
            boundaryProcs[patch.first] = stoi(patchInfo.at("neighbProcNo"));
        }
    }
}
void Matop::heat_equation(RCF *rcf, const arrType<uscalar, nrhs> u, const uvec DT, const uscalar dt, arrType<uscalar, nrhs>& un) {
    const Mesh& mesh = *(rcf->mesh);
    Vec x, b;
    Mat A;

    integer n = mesh.nInternalCells;
    integer il, ih;
    integer jl, jh;

    MatCreate(PETSC_COMM_WORLD, &A);
    MatSetSizes(A, n, n, PETSC_DETERMINE, PETSC_DETERMINE);
    MatSetType(A, "aij");
    //MatSetFromOptions(A);
    if (mesh.nProcs > 1) {
        MatMPIAIJSetPreallocation(A, 7, NULL, 6, NULL);
    } else {
        MatSeqAIJSetPreallocation(A, 7, NULL);
    }
    //MatSetOption(A, MAT_NEW_NONZERO_ALLOCATION_ERR, PETSC_FALSE);
    MatGetOwnershipRange(A, &il, &ih);
    MatGetOwnershipRangeColumn(A, &jl, &jh);

    uvec faceData(mesh.nFaces);
    for (integer j = 0; j < mesh.nFaces; j++) {
        faceData(j) = mesh.areas(j).value()*DT(j)/mesh.deltas(j).value();
    }

    for (integer j = il; j < ih; j++) {
        integer index = j-il;
        uscalar neighbourData[6];
        uscalar cellData = 0;
        integer cols[6];
        for (integer k = 0; k < 6; k++) {
            integer f = mesh.cellFaces(index, k);
            neighbourData[k] = -faceData(f)/mesh.volumes(index).value();
            cols[k] = mesh.cellNeighbours(index, k);
            if (cols[k] > -1) {
                cols[k] += jl;
            } 
            if ((cols[k] > -1) || (f >= mesh.nLocalFaces)) {
                cellData -= neighbourData[k];
            }
        }
        MatSetValues(A, 1, &j, 6, cols, neighbourData, INSERT_VALUES);
        MatSetValue(A, j, index + jl, cellData + 1./dt, INSERT_VALUES);
    }


    const integer* ranges = new integer[mesh.nProcs+1];
    MatGetOwnershipRangesColumn(A, &ranges);

    for (auto& patch: boundaryNeighbours) {
        auto& neighbourIndices = patch.second;
        integer startFace, nFaces;
        tie(startFace, nFaces) = mesh.boundaryFaces.at(patch.first);
        integer proc = boundaryProcs.at(patch.first);//stoi(patchInfo.at("neighbProcNo"));
        for (integer j = 0; j < nFaces; j++) {
            integer f = startFace + j;
            integer p = mesh.owner(f);
            integer index = il + p;
            integer neighbourIndex = ranges[proc] + neighbourIndices(j);
            uscalar data = -faceData(f)/mesh.volumes(p).value();
            MatSetValue(A, index, neighbourIndex, data, INSERT_VALUES);
        }
    } 
    delete[] ranges;

    MatAssemblyBegin(A,MAT_FINAL_ASSEMBLY);
    MatAssemblyEnd(A,MAT_FINAL_ASSEMBLY);
    
    KSP ksp;
    PC pc;
    //KSPSetFromOptions(ksp);
    KSPCreate(PETSC_COMM_WORLD, &(ksp));
    //KSPSetType(ksp, "mumps");
    KSPSetType(ksp, "gmres");
    KSPGetPC(ksp, &(pc));
    PCSetType(pc, "hypre");
    KSPSetOperators(ksp, A, A);
    //KSPSetFromOptions(ksp);
    KSPSetUp(ksp);

    MatCreateVecs(A, &x, &b);
    uscalar *data1 = new uscalar[n];
    VecPlaceArray(b, data1);
    for (integer i = 0; i < nrhs; i++) {
        for (integer j = 0; j < n; j++) {
            data1[j] = u(j, i)/dt;
        }
        KSPSolve(ksp, b, x);
        uscalar *data2;
        VecGetArray(x, &data2);
        for (integer j = 0; j < n; j++) {
            un(j, i) = data2[j];
        }
        VecRestoreArray(x, &data2);
    }
    VecResetArray(b);
    delete[] data1;

    //KSPDestroy(&ksp);
    VecDestroy(&b);
    VecDestroy(&x);
    MatDestroy(&A);
}

